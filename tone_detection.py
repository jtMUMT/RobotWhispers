import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
import pyo

QUIT = False

# This will contain all the pitch analysis code
def RunPitchAnalysis(buffer):
    global QUIT
    print('analyzing...')
    # x = input("record again? (y/n)")
    # if (x == 'y'):
    #     print("recording...")
    # else:
    #     QUIT = True



# Initialize pyo server and whatnot
# Use Jack audio protocol, use 1 audio channel (mono)
audio_server = pyo.Server(nchnls=1)
audio_server.boot()
audio_server.start()
# Make a very simple tone generator with envelope
# tone_env = pyo.Adsr()
# tone_synth = pyo.Sine(freq=500,mul=tone_env)
# Input buffer for recording live input
# input_buffer = pyo.NewTable(length=1,chnls=1)
audio_input=pyo.Input(chnl=1).out()
# audio_recorder = pyo.TableRec(audio_input,input_buffer)
# audio_playback = pyo.TableRead(input_buffer)
# # Trigger processing function when input recording is finished
# analysis_trigger = pyo.TrigFunc(audio_recorder['trig'],RunPitchAnalysis,input_buffer)
# playback_trigger = pyo.TrigFunc(audio_recorder['trig'],audio_playback.play)

# # Run the pyo input/output test
# x = input("Press Enter when ready to start recording:")
# audio_recorder.play()

# while not QUIT:
#     x = 0 # dummy operation

# print("quitting")
# audio_server.stop()

audio_server.gui(locals())
    

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