import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

samplerate, data = wavfile.read('testdata/sin250.wav')
# samplerate, data = wavfile.read('testdata/sin500.wav')
# samplerate, data = wavfile.read('testdata/sin500_noise18.wav')
# samplerate, data = wavfile.read('testdata/sin500_noise0.wav')
# samplerate, data = wavfile.read('testdata/sine500_noise6_multi.wav')

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
offset_level = 0.2
sampdiffs = [0]
smoothing_factor = 1/100
start = 0
end = int(samplerate / 2)
simple_posedgecount = 0
simple_pitch_estimate = 0
pitch_scaling = 1000
pitch_env = []
last_edge = 0
pulse_width_pitch_est = 0
pitch_smoothing_factor = 1/441
pitch_env_smooth = []

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
            if ((crossings[s-1] + crossings[s]) == 0): #any edge
                simple_posedgecount += 1
                onset_duration = s - onset_start
                # print(simple_posedgecount,onset_duration)
                simple_pitch_estimate = simple_posedgecount / 2 / onset_duration * samplerate
                pulse_width = s - last_edge
                print(pulse_width)
                pulse_width_pitch_est = 1/((pulse_width) / samplerate)/2
                last_edge = s
                # print(pulse_width_pitch_est)
            pitch_env.append(pulse_width_pitch_est)
            pitch_env_smooth.append(pitch_env_smooth[s-1] + (pitch_smoothing_factor*(pulse_width_pitch_est - pitch_env_smooth[s-1])))
    else:
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


plt.figure()
plt.plot(data[start:end])
# plt.plot(crossings[start:end])
# plt.plot(rectified[start:end])
plt.plot(envelope[start:end])
plt.plot(envelope_binary[start:end])
# plt.plot(sampdiffs[start:end])
plt.plot(np.asarray(pitch_env[start:end])/pitch_scaling)
plt.plot(np.asarray(pitch_env_smooth[start:end])/pitch_scaling)
plt.show()