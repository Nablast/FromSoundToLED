# Will Yager
# This Python script sends color/brightness data based on
# ambient sound frequencies to the LEDs.

import numpy as np
from math import pi, atan
import math
import scipy.signal

class SpectrumComputer:

    def __init__(self, numSpectrumBands, sample_rate, Chunk):

        self.numSpectrumBands = numSpectrumBands
        self.last_sample = np.zeros((numSpectrumBands,), dtype=np.float)
        self.sample_rate = sample_rate

        # Equation to map the N values to spectrumValues
        # 10^(C*SpectrumLength) = N (pour trouver C)
        N = Chunk/2
        C = math.log10(N)/numSpectrumBands
        self.indicesInFFT = [math.pow(10,i*C) for i in range(numSpectrumBands)]
        result = np.zeros((numSpectrumBands,), dtype=np.float)
        for i in range(numSpectrumBands):
            self.indicesInFFT[i] = max(i,int(self.indicesInFFT[i]))

        
        frequencies = [float(sample_rate*i)/Chunk for i in range(numSpectrumBands)]
        self.human_ear_multipliers = np.array([self.human_hearing_multiplier(f) for f in frequencies])

        self.processFilter = False

    def setFilter(self,type,freq1,freq2=0):

        self.processFilter = True
        order = 3
        nyq = 0.5 * self.sample_rate
        normal_cutoff = freq1 / nyq
        self.b, self.a = scipy.signal.butter(order, normal_cutoff, btype=type, analog=False)
        
    def fft(self, audio_Sample):

        def filterAudio(audio):
            #cumsum = np.cumsum(np.insert(audio,0,0))
            #return (cumsum[windowSize:] - cumsum[:-windowSize]) / windowSize
            return scipy.signal.lfilter(self.b, self.a, audio)
            
        l = audio_Sample[0]
        r = audio_Sample[1]
        
        return np.abs(np.fft.rfft(l)) + np.abs(np.fft.rfft(r))
            
        # Test filter
        # return np.abs(np.fft.rfft(filterAudio(l))) + np.abs(np.fft.rfft(filterAudio(r)))

    def scale_samples(self, fft_sample):
        return np.array([fft_sample[self.indicesInFFT[i]] for i in range(self.numSpectrumBands)])

    def rolling_smooth(self, array_sample, falloff):

        smooth = self.last_sample*falloff
        smooth += array_sample * (1.0 - falloff)
        self.last_sample = smooth
        return smooth

    def add_white_noise(self, array, amount):
        if sum(array) != 0:
            return array + amount
        else:
            return array

    def exaggerate(self, array, exponent):
        return array ** exponent

    def human_hearing_multiplier(self, freq):
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

    def schur(self, array, multipliers):
        return array*multipliers

    def rolling_scale_to_max(self, array, falloff):
        avg_peak = 0.0
        peak = np.max(array)
        if peak > avg_peak:
            avg_peak = peak # Output never exceeds 1
        else:
            avg_peak *= falloff
            avg_peak += peak * (1-falloff)
        if avg_peak == 0:
            return array
        else:
            return array / avg_peak

    # [[Float 0.0-1.0 x 32]]
    def process(self, audio_sample):
        
        notes = self.fft(audio_sample)
        notes = self.scale_samples(notes)
        notes = self.add_white_noise(notes, amount=2000)
        notes = self.schur(notes, self.human_ear_multipliers)
        notes = self.rolling_scale_to_max(notes, falloff=.98) # Range: 0-1
        notes = self.exaggerate(notes, exponent=2)
        notes = self.rolling_smooth(notes, falloff=.5)
        return notes