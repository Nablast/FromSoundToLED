# Will Yager
# This Python script sends color/brightness data based on
# ambient sound frequencies to the LEDs.

import numpy as np
from math import pi, atan
import math
import scipy.signal

class SpectrumComputer:

    def __init__(self, sample_rate, Chunk):

        self.last_sample = np.zeros((int(Chunk/2),), dtype=np.float)
        self.sample_rate = sample_rate

        frequencies = [float(sample_rate*i)/Chunk for i in range(1,int(Chunk/2)+1)]
        self.human_ear_multipliers = np.array([self.human_hearing_multiplier(f) for f in frequencies])

        self.avg_peak = 0.0
        
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
            
        # audio_Sample[0] : Left Channel
        # audio_Sample[1] : Right Channel
        # Rfft => return only real part of fft (size = len(audio_Sample) / 2)
        
        return np.abs(np.fft.rfft(audio_Sample[0]))[1:] + np.abs(np.fft.rfft(audio_Sample[1])[1:])
            
        # Test filter
        # return np.abs(np.fft.rfft(filterAudio(l))) + np.abs(np.fft.rfft(filterAudio(r)))

    def add_white_noise(self, array, amount):
        if sum(array) != 0:
            return array + amount
        else:
            return array

    def human_hearing_multiplier(self, freq):
        points = {0:-10, 50:-8, 100:-4, 200:0, 500:2, 1000:0, \
                    2000:2, 5000:4, 10000:-4, 15000:0, 20000:-4,40000:-4}
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

    def process(self, audio_sample):
        
        # Real fft on left and right, then add
        notes = self.fft(audio_sample)
        
        # Add white noise to the signal to drown noise out on quiet parts
        notes = self.add_white_noise(notes, amount=2000)
        
        # Arrange frequencies in terms of human ear
        # notes = self.schur(notes, self.human_ear_multipliers)
        
        return notes