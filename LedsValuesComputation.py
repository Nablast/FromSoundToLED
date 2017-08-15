
import numpy as np
import scipy.signal

decreaseMaxByTime = 0.0005
increaseMinByTime = 0.0005

from notes_scaled_nosaturation_Original import SpectrumComputer

class LedsValuesComputation:

    def __init__(self, nbLeds, numSpectrumBands, rate, chunk, buttonStates, threashL, threashU):
        
        self.nbLeds = nbLeds
        
        self.min = [1] * nbLeds
        self.max = [0] * nbLeds

        self.threashL = threashL
        self.threashU = threashU

        self.spectrumComputer = SpectrumComputer(numSpectrumBands, rate, chunk)
        
        self.buttonStates = buttonStates
        
    def setButtonStates(self, buttonStates):
    
        self.buttonStates = buttonStates
        
    def computeLedsValueFromSpectrum(self, spectrum):
    
        self.maxChanged = [False]*self.nbLeds
        self.minChanged = [False]*self.nbLeds
        
        result = []
       
        # Process for each led
        for iLed in range(self.nbLeds):
        
            currentMax = 0
            # For each Led : get max and min on values checked by buttons
            for i,v in enumerate(spectrum):
            
                if (self.buttonStates[iLed][i]):
                
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
                
        return result
        
    def process(self, audioSamples, returnOnlyLedsValues = False):
    
        for i, audioSample in enumerate(audioSamples):
        
            spectrum = self.spectrumComputer.process(audioSample)  
            
            ledsValues = self.computeLedsValueFromSpectrum(spectrum)
            
            if returnOnlyLedsValues:
                yield ledsValues
            else:
                yield spectrum, ledsValues, self.max, self.min, max(audioSample[0])
