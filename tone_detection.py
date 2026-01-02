import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
import pyo

QUIT = False
RUN_ANALYSIS = False
PLAY_NEXT = False
PLAYBACK_FINISHED = False

# This will contain all the pitch analysis code
def RunPitchAnalysis(data):
    global RUN_ANALYSIS
    RUN_ANALYSIS = True

def PlayNextNote():
    global PLAY_NEXT
    PLAY_NEXT = True

def StartOutputTone(envelope):
    print("start tone")
    envelope.play()

def StopOutputTone(envelope):
    print("stop tone")
    envelope.stop()

def StopRecording(recorders):
    print("stop recording")
    recorders[0].stop()
    recorders[1].stop()

def ConcludePlayback():
    global PLAYBACK_FINISHED
    PLAYBACK_FINISHED = True

# Initialize pyo server and whatnot
# Use Jack audio protocol, use 1 audio channel (mono)
audio_server = pyo.Server(sr=44100, buffersize=512, nchnls=2)
audio_server.boot()
audio_server.start()

# Make a very simple tone generator with envelope
tone_env = pyo.Adsr(attack=0.1,decay=0,sustain=1.0,release=0.1,mul=0.3)


# Input buffer for recording live input
input_buffer = pyo.NewTable(length=3,chnls=1)
trig_buffer = pyo.NewTable(length=3,chnls=2)

audio_input=pyo.Input(chnl=1)
audio_recorder = pyo.TableRec(audio_input,input_buffer)

input_follower = pyo.Follower(audio_input)

# Set up the audio-rate onset detectors (will stand-in for the offline analysis)
onset_detector = pyo.Thresh(input_follower,threshold=0.5,dir=0) # positive edge detector
release_detector = pyo.Thresh(input_follower,threshold=0.05,dir=1) # negative edge detector
onset_gate_enable = pyo.Trig()
release_gate_enable = pyo.Trig()
release_gate = pyo.NextTrig(release_detector,release_gate_enable) # one-shot trigger that sends the next detected release
onset_gate = pyo.NextTrig(onset_detector,release_gate + onset_gate_enable) # one-shot trigger that sends the next detected onset
release_gate.setInput2(onset_gate + release_gate_enable)

timeout_counter = pyo.Count(release_gate).stop()
timeout_value = int(44100*2) # stop recording 2 seconds after the last detected release #FIXME: hardcoded sampling rate and timeout
timeout_trigger = pyo.Compare(timeout_counter,timeout_value,mode=">=")
trig_recorder = pyo.TableRec([onset_gate,release_gate],trig_buffer)
timeout_func = pyo.TrigFunc(timeout_trigger,StopRecording,(audio_recorder,trig_recorder))
audio_playback_env = pyo.Adsr(sustain=1.0)
audio_playback = pyo.TableRead([input_buffer,input_buffer],freq=input_buffer.getRate(),loop=0,mul=audio_playback_env).out()

trigger_playback = pyo.TableRead(trig_buffer,freq=trig_buffer.getRate(),loop=0,mul=1).out()
trig_finish_indicator = pyo.TrigFunc(trigger_playback['trig'],ConcludePlayback)
toneout_onset_trigger = pyo.TrigFunc(trigger_playback[0],StartOutputTone,tone_env)
toneout_freqs = [500] # fill this in during anlaysis
toneout_freqswitcher = pyo.Iter(trigger_playback[0],toneout_freqs)
toneout_release_trigger = pyo.TrigFunc(trigger_playback[1],StopOutputTone,tone_env)

tone_synth = pyo.Sine(freq=[toneout_freqswitcher,toneout_freqswitcher],mul=tone_env).out()

# # Trigger processing function when input recording is finished
analysis_trigger = pyo.TrigFunc(audio_recorder['trig'],RunPitchAnalysis,audio_input)
# playback_trigger = pyo.TrigFunc(audio_recorder['trig'],audio_playback.play)

# # Run the pyo input/output test
x = input("Press Enter when ready to start recording:")

# start listening until timeout or buffer full:
onset_gate_enable.play() # record detected onsets
audio_recorder.play() # record input audio

while not QUIT:
    if RUN_ANALYSIS:
        print('analyzing...')
        # audio_playback.play()
        # audio_playback_env.play()
        # plt.figure()
        # plt.plot(input_buffer.getTable())
        # plt.show(block=False)

        samplerate = audio_server.getSamplingRate()
        data = input_buffer.getTable()
        data = data/np.max(data)
        rectified = np.abs(data)

        crossings = []

        envelope = [0]
        envelope_binary = [0]
        onset_level = 0.3
        onset_start = None
        note_on = False
        new_note = False
        new_off = False
        offset_level = 0.05
        sampdiffs = [0]
        smoothing_factor = 1/100
        start = 0
        # end = int(samplerate / 2)
        end = len(data)
        simple_posedgecount = 0
        simple_pitch_estimate = 0
        pitch_scaling = 1000
        pitch_env = []
        last_pos_edge = 0
        pulse_width_pitch_est = 0
        pitch_smoothing_factor = 1/441
        pitch_env_smooth = []
        minimum_allowed_pitch = 100

        detected_pulses = []
        this_pulse = {}

        pulse_start = 0
        pulse_end = 0

        wait_for_neg_edge = False

        # set freq bounds for noise rejection
        maximum_pitch = 4000 #Hz
        minimum_pulsewidth = int(samplerate/maximum_pitch)

        for s in range((end-start)):

            if (data[s] >= 0):
                crossings.append(1)
            else:
                crossings.append(-1)

            if (s == len(data)-1) and (note_on):
                new_off = True
                note_on = False

            if (s > 1) and (note_on):
                if (new_note):
                    this_pulse = {}
                    new_note = False
                    onset_start = s
                    this_pulse['start'] = onset_start
                    pitch_env.append(0)
                    pitch_env_smooth.append(0)
                else:
                    if ((crossings[s] - crossings[s-1]) > 0): #pos. edge
                        pulse_start = s
                    elif ((crossings[s] - crossings[s-1]) < 0): # neg. edge
                        pulse_end = s
                        onset_duration = s - onset_start
                        pulse_width = pulse_end - pulse_start
                        if (pulse_width > minimum_pulsewidth):
                            simple_posedgecount += 1
                            cycle_period = s - last_pos_edge
                            # print(simple_posedgecount,onset_duration)
                            simple_pitch_estimate = simple_posedgecount / onset_duration * samplerate
                            # print(pulse_width)
                            pulse_width_pitch_est = 1/((cycle_period) / samplerate)
                            last_pos_edge = s
                            # print(pulse_width_pitch_est)
                    pitch_env.append(simple_pitch_estimate)
                    pitch_env_smooth.append(pitch_env_smooth[s-1] + (pitch_smoothing_factor*(pulse_width_pitch_est - pitch_env_smooth[s-1])))
            else:
                if (new_off):
                    new_off = False
                    this_pulse['end'] = s
                    this_pulse['duration'] = this_pulse['end'] - this_pulse['start']
                    median_pitch_est = np.median(pitch_env_smooth[onset_start:s])
                    # print(median_pitch_est)
                    if (median_pitch_est > minimum_allowed_pitch):
                        this_pulse['pitch_median'] = median_pitch_est
                        print(this_pulse)
                        detected_pulses.append(this_pulse)
                        # print(detected_pulses)
                pitch_env.append(0)
                pitch_env_smooth.append(0)

            if (s > 0):
                sampdiff = rectified[s] - envelope[s-1]
                sampdiffs.append(sampdiff)
                envelope.append(envelope[s-1] + (smoothing_factor*sampdiff) * 2)
                if (note_on):
                    if (envelope[s] < offset_level):
                        envelope_binary.append(0)
                        note_on = False
                        new_off = True
                        simple_posedgecount = 0 # reset the zero count
                    else:
                        envelope_binary.append(1)
                else:
                    if (envelope[s] > onset_level):
                        envelope_binary.append(1)
                        note_on = True
                        new_note = True
                    else:
                        envelope_binary.append(0)

        # median_pitch_est = np.median(pitch_env_smooth[onset_start:s])
        # print(this_pulse)

        rest_length = 0.5 #seconds

        # print("all pulses: ", detected_pulses)

        inter_tone_intervals = []
        # calculate event timings
        for i in range(len(detected_pulses)):
            if (i > 0):
                interval = (detected_pulses[i]['start'] - detected_pulses[i-1]['end']) / samplerate
                inter_tone_intervals.append(interval)
            else:
                inter_tone_intervals.append(0)
        print(inter_tone_intervals)
        event_count = 0

        toneout_freqs = []
        for p in detected_pulses:
            toneout_freqs.append(p['pitch_median']) # add this pitch to the list of pitches to play
        print(toneout_freqs)
        toneout_freqswitcher.setChoice(toneout_freqs)
        #     print("Playing:", p)
        #     pdur = p['duration']/samplerate

        #     inter_dur = inter_tone_intervals[event_count]
        #     event_count += 1
        #     # pdur = 1
        #     tone_synth.setFreq(float(p['pitch_median']))
        #     tone_env.setDur(pdur)
        #     tone_env.play()

        #     #rest between notes if needed
        #     if (inter_dur > 0):
        #         PLAY_NEXT = False
        #         a = pyo.CallAfter(PlayNextNote,inter_dur,None)
        #         while not PLAY_NEXT:
        #             x = 0

        #     #play the note for its indicated duration
        #     PLAY_NEXT = False
        #     a = pyo.CallAfter(PlayNextNote,pdur,None)
        #     while not PLAY_NEXT:
        #         x = 0
        #     # tone_env.stop()

        # # Wait for a moment before plotting
        # PLAY_NEXT = False
        # a = pyo.CallAfter(PlayNextNote,1,None)
        # while not PLAY_NEXT:
        #     x = 0

        # plt.figure()
        # # plt.plot(data[start:end],label='data')
        # # plt.plot(crossings[start:end],label='cross')
        # # plt.plot(rectified[start:end])
        # plt.plot(envelope[start:end],label='env')
        # plt.plot(envelope_binary[start:end],label='thresh')
        # # plt.plot(sampdiffs[start:end])
        # # plt.plot(np.asarray(pitch_env[start:end])/pitch_scaling,label='pitch')
        # plt.plot(np.asarray(pitch_env_smooth[start:end])/pitch_scaling,label='pitch_smooth')
        # plt.legend()
        # plt.show()

        PLAYBACK_FINISHED = False
        trigger_playback.out()
        while not PLAYBACK_FINISHED:
            x = 0
        x = input("finished playback")
            

        x = input("record again? (y/n)")
        if (x == 'y'):
            print("recording...")
            audio_recorder.play()
            trig_recorder.play()
            RUN_ANALYSIS = False
        else:
            QUIT = True
        audio_playback_env.stop()

print("quitting")
audio_server.stop()

# audio_server.gui(locals())
    

# test_dir = 'testdata/'
# test_files = ['sin250.wav',
#               'sin500.wav',
#               'sin500_noise18.wav',
#               'sin500_noise0',
#               'sine500_noise6_multi',
#               'whistletest_01.wav']


# samplerate, data = wavfile.read(test_dir + test_files[5])

# print(samplerate)
# print(len(data)/samplerate)

# data = data/np.max(data)
# rectified = np.abs(data)

# crossings = []

# envelope = [0]
# envelope_binary = [0]
# onset_level = 0.3
# onset_start = None
# note_on = False
# new_note = False
# new_off = False
# offset_level = 0.05
# sampdiffs = [0]
# smoothing_factor = 1/100
# start = 0
# # end = int(samplerate / 2)
# end = len(data)
# simple_posedgecount = 0
# simple_pitch_estimate = 0
# pitch_scaling = 1000
# pitch_env = []
# last_pos_edge = 0
# pulse_width_pitch_est = 0
# pitch_smoothing_factor = 1/441
# pitch_env_smooth = []

# detected_pulses = []
# this_pulse = {}

# pulse_start = 0
# pulse_end = 0

# wait_for_neg_edge = False

# # set freq bounds for noise rejection
# maximum_pitch = 4000 #Hz
# minimum_pulsewidth = int(samplerate/maximum_pitch)

# for s in range((end-start)):

#     if (data[s] >= 0):
#         crossings.append(1)
#     else:
#         crossings.append(-1)

#     if (s == len(data)-1):
#         new_off = True
#         note_on = False

#     if (s > 1) and (note_on):
#         if (new_note):
#             this_pulse = {}
#             new_note = False
#             onset_start = s
#             this_pulse['start'] = onset_start
#             pitch_env.append(0)
#             pitch_env_smooth.append(0)
#         else:
#             if ((crossings[s] - crossings[s-1]) > 0): #pos. edge
#                 pulse_start = s
#             elif ((crossings[s] - crossings[s-1]) < 0): # neg. edge
#                 pulse_end = s
#                 onset_duration = s - onset_start
#                 pulse_width = pulse_end - pulse_start
#                 if (pulse_width > minimum_pulsewidth):
#                     simple_posedgecount += 1
#                     cycle_period = s - last_pos_edge
#                     # print(simple_posedgecount,onset_duration)
#                     simple_pitch_estimate = simple_posedgecount / onset_duration * samplerate
#                     # print(pulse_width)
#                     pulse_width_pitch_est = 1/((cycle_period) / samplerate)
#                     last_pos_edge = s
#                     # print(pulse_width_pitch_est)
#             pitch_env.append(simple_pitch_estimate)
#             pitch_env_smooth.append(pitch_env_smooth[s-1] + (pitch_smoothing_factor*(pulse_width_pitch_est - pitch_env_smooth[s-1])))
#     else:
#         if (new_off):
#             new_off = False
#             this_pulse['end'] = s
#             this_pulse['duration'] = this_pulse['end'] - this_pulse['start']
#             median_pitch_est = np.median(pitch_env_smooth[onset_start:s])
#             this_pulse['pitch_median'] = median_pitch_est
#             # print(median_pitch_est)
#             print(this_pulse)
#             detected_pulses.append(this_pulse)
#         pitch_env.append(0)
#         pitch_env_smooth.append(0)

#     if (s > 0):
#         sampdiff = rectified[s] - envelope[s-1]
#         sampdiffs.append(sampdiff)
#         envelope.append(envelope[s-1] + (smoothing_factor*sampdiff) * 2)
#         if (note_on):
#             if (envelope[s] < offset_level):
#                 envelope_binary.append(0)
#                 note_on = False
#                 new_off = True
#                 simple_posedgecount = 0 # reset the zero count
#             else:
#                 envelope_binary.append(1)
#         else:
#             if (envelope[s] > onset_level):
#                 envelope_binary.append(1)
#                 note_on = True
#                 new_note = True
#             else:
#                 envelope_binary.append(0)

# # median_pitch_est = np.median(pitch_env_smooth[onset_start:s])
# # print(this_pulse)

# # RENDER the detected tones as audio
# last_sample = detected_pulses[-1]['end']
# print(last_sample)
# outwav = np.zeros(last_sample)

# for p in detected_pulses:
#     s = p['start']
#     e = p['end']
#     d = p['duration']
#     print(s,d)
#     f = p['pitch_median']
#     for i in range(d):
#         outwav[s+i] = np.sin(f * 2 * np.pi *  (i/samplerate))
#         # outwav[s+i] = 1.0

# wavfile.write('test_output.wav', samplerate, outwav)
    

# plt.figure()
# # plt.plot(data[start:end],label='data')
# # plt.plot(crossings[start:end],label='cross')
# # plt.plot(rectified[start:end])
# plt.plot(envelope[start:end],label='env')
# plt.plot(envelope_binary[start:end],label='thresh')
# # plt.plot(sampdiffs[start:end])
# # plt.plot(np.asarray(pitch_env[start:end])/pitch_scaling,label='pitch')
# plt.plot(np.asarray(pitch_env_smooth[start:end])/pitch_scaling,label='pitch_smooth')
# plt.legend()
# plt.show()