
import numpy as np
import scipy.signal
import multiprocessing as mp

decreaseMaxByTime = 0.0001
increaseMinByTime = 0.0005

import time, math

current_milli_time = lambda: (time.time() * 1000.0)

from notes_scaled_nosaturation_Original import SpectrumComputer

class LedsValuesComputation:

    def __init__(self, rate, chunk, frequencySeparators, initSmoothness, threashL, threashU):
        
        self.nbLeds = len(frequencySeparators)
        self.spectrumLength = int(chunk/2)
        
        self.smoothnessByLed = initSmoothness
        self.lastLedMax = [0.0]*self.nbLeds
        self.lastLedMaxTime = [0.0]*self.nbLeds
        
        self.chunk = chunk
        self.rate = rate
        
        self.lockFrequenciesChanged = [mp.Lock() for i in range(self.nbLeds)]
        
        self.last_sample = [[1]]*self.nbLeds
        self.avg_peak = [0.0]*self.nbLeds
        
        self.min = [1] * self.nbLeds
        self.max = [0] * self.nbLeds
        
        self.cThreshL = [1]* self.nbLeds
        self.cThreshU = [0]* self.nbLeds

        self.threashL = threashL
        self.threashU = threashU

        self.spectrumComputer = []
        for iLed in range(self.nbLeds):
            self.spectrumComputer.append(SpectrumComputer(rate, chunk, frequencySeparators[iLed][0], frequencySeparators[iLed][1]))
        
        # self.spectrumComputer = SpectrumComputer(rate, chunk)
        
        self.frequencies = [rate*i/chunk for i in range(1,int(chunk/2)+1)]
        
        # We suppose that separators are in order
        # self.binsByLeds = [[]]*self.nbLeds
        # for indexBin in range(int(chunk/2)):
            # currentFreq = frequencies[indexBin]
            # for iLed in range(len(frequencySeparators)):
                # if currentFreq < frequencySeparators[iLed]:
                    # self.binsByLeds[iLed].append(indexBin)
                    # break
                # elif currentFreq > frequencySeparators[-1]:
                    # self.binsByLeds[-1].append(indexBin)
                    
        self.ledByBins = [-2]*int(chunk/2)
        for indexBin in range(int(chunk/2)):
            currentFreq = self.frequencies[indexBin]
            for iLed in range(len(frequencySeparators)):
                if currentFreq >= frequencySeparators[iLed][0] and currentFreq < frequencySeparators[iLed][1]:
                    self.ledByBins[indexBin] = iLed
        
    def setFrequencySeparators(self, iLed, min, max):
        self.lockFrequenciesChanged[iLed].acquire()
        
        # Set Filter of Spectrum Computer
        self.spectrumComputer[iLed].setFilter(min, max)
        
        # Update ledByBins vars
        for indexBin in range(int(self.chunk/2)):
            currentFreq = self.frequencies[indexBin]
            
            if self.ledByBins[indexBin] == iLed:
                self.ledByBins[indexBin] = -2
            if currentFreq >= min and currentFreq < max:
                self.ledByBins[indexBin] = iLed
                
        self.lockFrequenciesChanged[iLed].release()
        
    def setSmoothness(self, iLed, smoothness):
        
        self.smoothnessByLed[iLed] = smoothness
        
    def normalizeSpectrumByThreash(self, iLed, array, falloff):
    
        # If currentMax < max, we decrease max by (max-currentMax)*(1-falloff)
        # We return value in [0,1] 1 set to the max
        
        result = []
    
        currentMaxByLed = 0.0
        for iBin, v in enumerate(array):
            iCurrentLed = self.ledByBins[iBin]
            if iCurrentLed == iLed:
                result.append(array[iBin])
                if v > currentMaxByLed:
                    currentMaxByLed = v # Output never exceeds 1
                

        if currentMaxByLed > self.avg_peak[iLed]:
            self.avg_peak[iLed] = currentMaxByLed
        else:
            self.avg_peak[iLed] *= falloff
            self.avg_peak[iLed] += currentMaxByLed * (1.0-falloff)
        
        result = np.array(result)
        result = result / self.avg_peak[iLed]
            
        return result
            
    def exaggerateSpectrum(self, array, exponent):
        return array ** exponent
            
    def smoothSpectrum(self, iLed, array_sample, falloff):

        if len(self.last_sample[iLed]) == len(array_sample):
            smooth = self.last_sample[iLed]*falloff
            smooth += array_sample * (1.0 - falloff)
            self.last_sample[iLed] = smooth
            return smooth
        else:
            self.last_sample[iLed] = array_sample
            return array_sample
            
    def smoothLed(self, iLed, ledValue):
    
        # We want to decrease thtough the function : -A*x*x + B
        # We want to be at prevMax at t = 0.
        # We want to be at 0 at t = Smoothness
        # => f(0) = B = prevMax
        #    f(Smoothness) = -A*Smoothness² + B = 0
        # 
        # => A = prevMax / Smoothness²
        #    B = prevMax 
        
        
        prevMax = self.lastLedMax[iLed]
        
        if ledValue < prevMax :
        
            if self.smoothnessByLed[iLed] > 0:
                t = current_milli_time() - self.lastLedMaxTime[iLed]
                A = prevMax / (self.smoothnessByLed[iLed]*self.smoothnessByLed[iLed])
                
                ledValue = max(- A*t*t + prevMax,0.0)
        else:
            self.lastLedMax[iLed] = ledValue
            self.lastLedMaxTime[iLed] = current_milli_time()
        
        return ledValue
        
    def computeLedsValueFromSpectrum(self, spectrum, iLed):
    
        maxChanged = False
        minChanged = False
        
        ledValueResult = 0.0
        
        # For each Led : get max and min on spectrum frequency range dedicated
        for i,v in enumerate(spectrum):
        
            if (v > ledValueResult):
                ledValueResult = v
            
            if (v > self.max[iLed]):
                self.max[iLed] = v
                maxChanged = True
            elif (v < self.min[iLed]):
                self.min[iLed] = v
                minChanged = True
                
                
        # Define lower and uppert threash in terms of min and max
        self.cThreshL[iLed] = self.min[iLed] + self.threashL[iLed] * (self.max[iLed] - self.min[iLed])
        
        self.cThreshU[iLed] = self.max[iLed] - self.threashU[iLed] * (self.max[iLed] - self.min[iLed])
            
        if ledValueResult < self.cThreshL[iLed]:
            ledValueResult = 0.0
        elif ledValueResult > self.cThreshU[iLed]:
            ledValueResult = 1.0
        
        # If max not changed : decrease it     
        if not maxChanged:
            self.max[iLed] = self.max[iLed] - decreaseMaxByTime
            
        # If min not changed : increase it     
        if not minChanged:
            self.min[iLed] = self.min[iLed] + increaseMinByTime
                
        return ledValueResult
        
    def process(self, audioSamples, returnOnlyLedsValues = False):
    
        for audioSample in audioSamples:
        
            ledsValues = [0.0]*self.nbLeds
            spectrums = [None]*self.nbLeds
            finalSpectrum = [0.0]*self.spectrumLength
            
            for iLed in range(self.nbLeds):
            
                self.lockFrequenciesChanged[iLed].acquire()
            
                # Return Spectrum : 
                #    - Values not normalized !!
                #    - Size = len(audioSample)/2
                spectrums[iLed] = self.spectrumComputer[iLed].process(audioSample) 
                

                # Ajust all spectrum magnitudes to the max of these magnitudes (normalization)
                # falloff is used for keeping quiet parts less bright than loud parts
                # It s like a dynamic threashold
                # Output returns ONLY bins which are between frequency separators
                spectrums[iLed] = self.normalizeSpectrumByThreash(iLed, spectrums[iLed], falloff=.98) # Range: 0-1
                
                # Square output : lower small values
                # The more a magnitude is high, the less the magnitude is lowered.
                # See square x curve.
                spectrums[iLed] = self.exaggerateSpectrum(spectrums[iLed], exponent=2)
            
                # Smooth spectrum
                spectrums[iLed] = self.smoothSpectrum(iLed, spectrums[iLed], falloff=0.3)
                               
                # Compute ledsValue in terms of spectrum
                ledsValues[iLed] = self.computeLedsValueFromSpectrum(spectrums[iLed], iLed)
                
                ledsValues[iLed] = self.smoothLed(iLed, ledsValues[iLed])
                
                self.lockFrequenciesChanged[iLed].release()
                
            if returnOnlyLedsValues:
                yield ledsValues
            else:
                yield spectrums, ledsValues, self.max, self.min, self.cThreshL, self.cThreshU, max(audioSample[0])
