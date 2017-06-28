
import numpy as np
import scipy.signal

decreaseMaxByTime = 0.0005
increaseMinByTime = 0.0005

defaultThreashL = 0.1
defaultThreashU = 0.15

releaseLed0 = 0.7

from notes_scaled_nosaturation_Original import SpectrumComputer

class LedsValuesComputation:

    def __init__(self, nbLeds, numSpectrumBands, rate, chunk):
        
        self.nbLeds = nbLeds
        
        self.min = [1] * nbLeds
        self.max = [0] * nbLeds

        self.threashL = [0.05] * nbLeds
        self.threashU = [0.2] * nbLeds

        self.spectrumComputer = SpectrumComputer(numSpectrumBands, rate, chunk)
        
        self.lastLed0Value = 0
        
    def computeLedsValueFromSpectrum(self, spectrum,selectedBandsOnSpectrum):
    
        self.maxChanged = [False]*self.nbLeds
        self.minChanged = [False]*self.nbLeds
        
        result = []
       
        # Process for each led
        for iLed in range(self.nbLeds):
        
            currentMax = 0
            # For each Led : get max and min on values checked by buttons
            for i,v in enumerate(spectrum):
                if (selectedBandsOnSpectrum[iLed][i]):
                    if (v > self.max[iLed]):
                        self.max[iLed] = v
                        self.maxChanged[iLed] = True
                    elif (v < self.min[iLed]):
                        self.min[iLed] = v
                        self.minChanged[iLed] = True
                        
                    if (v > currentMax):
                        currentMax = v
                       
            # Define lower and uppert threash in terms of min and max
            cThreshL = self.min[iLed] + self.threashL[iLed]
            cThreshU = self.max[iLed] - self.threashU[iLed]
            
            if currentMax < cThreshL:
                result.append(0)
            elif currentMax > cThreshU:
                result.append(1)
            else:
                result.append((currentMax - cThreshL)/(cThreshU - cThreshL))
            
            # If max not changed : decrease it     
            if not self.maxChanged[iLed]:
                self.max[iLed] = self.max[iLed] - decreaseMaxByTime
                
            # If min not changed : increase it     
            if not self.minChanged[iLed]:
                self.min[iLed] = self.min[iLed] + increaseMinByTime
                
                
        # Release on Led0
        if result[0] < self.lastLed0Value:
			result[0] = (result[0]*(1. - releaseLed0)*(1. - releaseLed0) + self.lastLed0Value*releaseLed0*releaseLed0)     
        self.lastLed0Value = result[0]
                
        return result
        
    def process(self, AudioGenerator, returnOnlyLedsValues = False):
    
        for i,(audioSample,selectedBandsOnSpectrum) in enumerate(AudioGenerator):
        
            spectrum = self.spectrumComputer.process(audioSample)  
            
            ledsValues = self.computeLedsValueFromSpectrum(spectrum,selectedBandsOnSpectrum)
            
            if returnOnlyLedsValues:
                yield ledsValues
            else:
                yield spectrum, ledsValues, self.max, self.min, max(audioSample[0])
