# Will Yager
# This Python script sends color/brightness data based on
# ambient sound frequencies to the LEDs.

import numpy as np
from math import pi, atan
import math
import scipy.signal

rate = 44100
cutOffFrequency = 1000.0
freqRatio = (cutOffFrequency/rate)
N = int(math.sqrt(0.196196 + freqRatio**2)/freqRatio)

nyq = 0.5 * rate
normal_cutoff = cutOffFrequency / nyq
order = 3
b, a = scipy.signal.butter(order, normal_cutoff, btype='high', analog=False)

def fft(audio_stream):

    def filterAudio(audio):
        #cumsum = np.cumsum(np.insert(audio,0,0))
        #return (cumsum[windowSize:] - cumsum[:-windowSize]) / windowSize
        return scipy.signal.lfilter(b, a, audio)
        
    for l, r in audio_stream:
        yield np.abs(np.fft.rfft(l)) + np.abs(np.fft.rfft(r))
        
        # Test filter
        # yield np.abs(np.fft.rfft(filterAudio(l))) + np.abs(np.fft.rfft(filterAudio(r)))

def scale_samples(fft_stream):
    for notes in fft_stream:
        yield notes[0:64]

def rolling_smooth(array_stream, falloff):
    smooth = next(array_stream)
    yield smooth
    for array in array_stream:
        smooth *= falloff
        smooth += array * (1 - falloff)
        yield smooth

def add_white_noise(array_stream, amount):
    for array in array_stream:
        if sum(array) != 0:
            yield array + amount
        else:
            yield array

def exaggerate(array_stream, exponent):
    for array in array_stream:
        yield array ** exponent

def human_hearing_multiplier(freq):
    points = {0:-10, 50:-8, 100:-4, 200:0, 500:2, 1000:0, \
                2000:2, 5000:4, 10000:-4, 15000:0, 20000:-4}
    freqs = sorted(points.keys())
    for i in range(len(freqs)-1):
        if freq >= freqs[i] and freq < freqs[i+1]:
            x1 = float(freqs[i])
            x2 = float(freqs[i+1])
            break
    y1, y2 = points[x1], points[x2]
    decibels = ((x2-freq)*y1 + (freq-x1)*y2)/(x2-x1)
    return 10.0**(decibels/10.0)

def schur(array_stream, multipliers):
    for array in array_stream:
        yield array*multipliers

def rolling_scale_to_max(stream, falloff):
    avg_peak = 0.0
    for array in stream:
        peak = np.max(array)
        if peak > avg_peak:
            avg_peak = peak # Output never exceeds 1
        else:
            avg_peak *= falloff
            avg_peak += peak * (1-falloff)
        if avg_peak == 0:
            yield array
        else:
            yield array / avg_peak

# [[Float 0.0-1.0 x 32]]
def process(audio_stream, num_leds, num_samples, sample_rate):
    frequencies = [float(sample_rate*i)/num_samples for i in range(num_leds)]
    human_ear_multipliers = np.array([human_hearing_multiplier(f) for f in frequencies])
    notes = fft(audio_stream)
    notes = scale_samples(notes)
    notes = add_white_noise(notes, amount=2000)
    notes = schur(notes, human_ear_multipliers)
    notes = rolling_scale_to_max(notes, falloff=.98) # Range: 0-1
    notes = exaggerate(notes, exponent=2)
    notes = rolling_smooth(notes, falloff=.7)
    return notes