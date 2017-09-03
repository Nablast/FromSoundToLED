
import numpy as np
import scipy.signal

decreaseMaxByTime = 0.0005
increaseMinByTime = 0.0005

from notes_scaled_nosaturation_Original import SpectrumComputer

def rolling_scale_to_max(self, array, falloff):
    
    peak = np.max(array)
    if peak > self.avg_peak:
        self.avg_peak = peak # Output never exceeds 1
    else:
        self.avg_peak *= falloff
        self.avg_peak += peak * (1-falloff)
    if self.avg_peak == 0:
        return array
    else:
        return array / self.avg_peak
        
def exaggerate(self, array, exponent):
    return array ** exponent
        
def rolling_smooth(self, array_sample, falloff):

    smooth = self.last_sample*falloff
    smooth += array_sample * (1.0 - falloff)
    self.last_sample = smooth
    return smooth

class LedsValuesComputation:

    def __init__(self, rate, chunk, frequencySeparators, threashL, threashU):
        
        self.nbLeds = len(frequencySeparators)+1
        
        self.min = [1] * self.nbLeds
        self.max = [0] * self.nbLeds

        self.threashL = threashL
        self.threashU = threashU

        self.spectrumComputer = SpectrumComputer(rate, chunk)
        
        frequencies = [rate*i/chunk for i in range(1,int(chunk/2)+1)]
        
        # We suppose that separators are in order
        self.binsByLeds = [[]*self.nbLeds]
        for indexBin in range(int(chunk/2)):
            currentFreq = frequencies[indexBin]
            for iLed in range(self.nbLeds):
                if currentFreq < frequencySeparatorsWithBounds[iLed]:
                    self.binsByLeds[iLed].append(indexBin)
                elif currentFreq > frequencySeparatorsWithBounds[-1]:
                    self.binsByLeds[-1].append(indexBin)
                    
                
        
    def computeLedsValueFromSpectrum(self, spectrum):
    
        maxChanged = [False]*self.nbLeds
        minChanged = [False]*self.nbLeds
        
        valuesByLed = [0.0]*self.nbLeds
        
        # For each Led : get max and min on spectrum frequency range dedicated
        for i,v in enumerate(spectrum):
        
            # LED index recognition from spectrum index
            currentLed = self.binsByLeds[i]
                
            if (v > valuesByLed[currentLed]):
                valuesByLed[currentLed] = v
            
            if (v > self.max[currentLed]):
                self.max[currentLed] = v
                maxChanged[currentLed] = True
            elif (v < self.min[currentLed]):
                self.min[currentLed] = v
                minChanged[currentLed] = True
            
        
        for iLed in range(self.nbLeds):
       
            # Define lower and uppert threash in terms of min and max
            cThreshL = self.min[iLed] + self.threashL[iLed]*self.min[iLed]
            cThreshU = self.max[iLed] - self.threashU[iLed]*self.max[iLed]
            
            if valuesByLed[iLed] < cThreshL:
                valuesByLed[iLed] = 0.0
            elif valuesByLed[iLed] > cThreshU:
                valuesByLed[iLed] = 1.0
            else:
                valuesByLed[iLed] = (valuesByLed[iLed] - cThreshL)/(cThreshU - cThreshL)
            
            # If max not changed : decrease it     
            if not maxChanged[iLed]:
                self.max[iLed] = self.max[iLed] - decreaseMaxByTime
                
            # If min not changed : increase it     
            if not minChanged[iLed]:
                self.min[iLed] = self.min[iLed] + increaseMinByTime
                
        return valuesByLed
        
    def process(self, audioSamples, returnOnlyLedsValues = False):
    
        for i, audioSample in enumerate(audioSamples):
        
            # Return Spectrum : 
            #    - Values not normalized !!
            #    - Size = len(audioSample)/2
            spectrum = self.spectrumComputer.process(audioSample) 
            
            # Ajust all spectrum magnitudes to the max of these magnitudes (normalization)
            # falloff is used for keeping quiet parts less bright than loud parts
            notes = self.rolling_scale_to_max(notes, falloff=.98) # Range: 0-1
            
            # Square output : lower small values
            # The more a magnitude is high, the less the magnitude is lowered.
            # See square x curve.
            notes = self.exaggerate(notes, exponent=2)
        
            # Smooth output
            notes = self.rolling_smooth(notes, falloff=.7)
            
            # Compute ledsValues in terms of spectrum
            ledsValues = self.computeLedsValueFromSpectrum(spectrum)
            
            if returnOnlyLedsValues:
                yield ledsValues
            else:
                yield spectrum, ledsValues, self.max, self.min, max(audioSample[0])
