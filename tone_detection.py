import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

# samplerate, data = wavfile.read('testdata/sin250.wav')
# samplerate, data = wavfile.read('testdata/sin500.wav')
# samplerate, data = wavfile.read('testdata/sin500_noise18.wav')
# samplerate, data = wavfile.read('testdata/sin500_noise0.wav')
samplerate, data = wavfile.read('testdata/sine500_noise6_multi.wav')

print(samplerate)
print(len(data)/samplerate)

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
offset_level = 0.2
sampdiffs = [0]
smoothing_factor = 1/100
start = 0
end = int(samplerate / 2)
simple_posedgecount = 0
simple_pitch_estimate = 0
pitch_scaling = 1000
pitch_env = []
last_pos_edge = 0
pulse_width_pitch_est = 0
pitch_smoothing_factor = 1/441
pitch_env_smooth = []

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

    if (s > 1) and (note_on):
        if (new_note):
            new_note = False
            onset_start = s
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
            median_pitch_est = np.median(pitch_env_smooth[onset_start:s])
            print(median_pitch_est)
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

median_pitch_est = np.median(pitch_env_smooth[onset_start:s])
print(median_pitch_est)

plt.figure()
# plt.plot(data[start:end])
plt.plot(crossings[start:end],label='cross')
# plt.plot(rectified[start:end])
plt.plot(envelope[start:end],label='env')
plt.plot(envelope_binary[start:end],label='thresh')
# plt.plot(sampdiffs[start:end])
plt.plot(np.asarray(pitch_env[start:end])/pitch_scaling,label='pitch')
plt.plot(np.asarray(pitch_env_smooth[start:end])/pitch_scaling,label='pitch_smooth')
plt.legend()
plt.show()