import sys
from PyQt4 import QtGui, QtCore
import pdb

import math
import pyaudio
import numpy as np
import pylab
import time
import wave
import matplotlib.pyplot as plt
from threading import Thread
from colorsys import hls_to_rgb
import scipy.signal

import notes_scaled_nosaturation, notes_scaled_nosaturation_Original

CHUNK = 1024

sizeWindows = 800
ratioSizeSquare = 0.15

ratioLines = 0.01
spaceBetweenLines = 0.005

numSpectrumBands = 64

smoothness = 70

threashold1 = 0.85
threashold2 = 0.5
threashold3 = 0.5

ledNumber = 3
ledColors = [QtGui.QColor(255, 0, 0), QtGui.QColor(0, 255, 0), QtGui.QColor(0, 0, 255)]

decreaseMaxByTime = 0.0005
increaseMinByTime = 0.0005

threashL = [0] * ledNumber
threashL[0] = 0.05
threashL[1] = 0.05
threashL[2] = 0.05
          
threashU = [0] * ledNumber
threashU[0] = 0.2
threashU[1] = 0.2
threashU[2] = 0.2
          
class changeSquaresThread(QtCore.QThread):

    def __init__(self, values):
        QtCore.QThread.__init__(self)
        self.values = values

    def __del__(self):
        self.wait()

    def run(self):
        self.emit(QtCore.SIGNAL("setSquares(PyQt_PyObject)"), self.values)
            
class changeSpectrumThread(QtCore.QThread):

    def __init__(self, values):
        QtCore.QThread.__init__(self)
        self.values = values

    def __del__(self):
        self.wait()
        
    def run(self):
        self.emit(QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.values)
     
class MyFirstGUI(QtGui.QWidget):

    def __init__(self):
        super(MyFirstGUI, self).__init__()
        self.resize(sizeWindows, sizeWindows)
        self.lastValues = [0 for x in range(numSpectrumBands)]
        self.initUI()
        
    def initUI(self):      

        # Button Read Audio
        but = QtGui.QPushButton('Read Audio', self)
        but.setCheckable(True)
        but.resize(0.2*sizeWindows,0.05*sizeWindows)
        h = sizeWindows*(1/10) - 0.05*sizeWindows/2
        w = sizeWindows*(1/2) - 0.2*sizeWindows/2
        but.move(w, h)
        but.clicked[bool].connect(self.readAudio)
    
        # Background
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette)
        
        self.col = QtGui.QColor(0, 0, 0)   
        
        # Squares Led
        self.squares = []
        squareSize = ratioSizeSquare*sizeWindows
        hSquares = sizeWindows*(5/6)
        for iLed in range(ledNumber):
            self.squares.append(QtGui.QFrame(self))
            self.squares[iLed].setGeometry(sizeWindows*((iLed+1)/(ledNumber+1)) - squareSize/2, hSquares - squareSize/2, squareSize, squareSize)
            self.squareRed.setStyleSheet("QWidget { background-color: %s }" % ledColors[iLed].name())
        
        # Spectrum
        self.hSpec = sizeWindows*(1/2)
        self.colWhite = QtGui.QColor(255, 255, 255)   
        self.spectrumLines = []
        self.wSpectrum = []
        self.hSpectrum = self.hSpec - ratioSizeSquare*5*sizeWindows/2
        for i in range(0,numSpectrumBands):
            self.spectrumLines.append(QtGui.QFrame(self))
            self.wSpectrum.append(sizeWindows*(1/2) + (i - numSpectrumBands/2)*(ratioLines+spaceBetweenLines)*sizeWindows)
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, 0, ratioLines*sizeWindows, 0 )
            self.spectrumLines[i].setStyleSheet("QWidget { background-color: %s }" % self.colWhite.name())
        
        # Buttons Below Spectrums
        self.buttonsForSquare = [[]] * ledNumber
        self.hButtons = [0] * ledNumber
        self.hButtons[0] = self.hSpec + ratioSizeSquare*sizeWindows/2 + spaceBetweenLines*sizeWindows
        for i in range(1,ledNumber):
            self.hButtons[i] = self.hButtons[i-1] + spaceBetweenLines*sizeWindows + ratioLines*sizeWindows
            
        for iLed in range(ledNumber):
            self.buttonsForSquare[iLed] = [None]*numSpectrumBands
            for i in range(numSpectrumBands):
                self.buttonsForSquare[iLed][i] = QtGui.QCheckBox("",self)
                self.buttonsForSquare[iLed][i].resize(ratioLines*sizeWindows,ratioLines*sizeWindows)
                self.buttonsForSquare[iLed][i].move(self.wSpectrum[i]-ratioLines*sizeWindows/2, self.hButtons[iLed] + ratioLines*sizeWindows/2)    
                
        # Min and Max on GUI
        self.heightMinMaxFrame = ratioSizeSquare*0.02
        self.guiTreasholdLMin = []
        self.guiTreasholdLMax = []
        for i in range(0,numSpectrumBands):
            self.guiTreasholdLMin.append([])
            self.guiTreasholdLMax.append([])
            for iLed in range(ledNumber):
                self.guiTreasholdLMin[i].append(QtGui.QFrame(self))
                self.guiTreasholdLMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, 0, ratioLines*sizeWindows, 0 )
                self.guiTreasholdLMin[i][iLed].setStyleSheet("QWidget { background-color: %s }" % ledColors[iLed].name())
                
                self.guiTreasholdLMax[i].append(QtGui.QFrame(self))
                self.guiTreasholdLMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, 0, ratioLines*sizeWindows, 0 )
                self.guiTreasholdLMax[i][iLed].setStyleSheet("QWidget { background-color: %s }" % ledColors[iLed].name())
            
        self.setWindowTitle('LED Simulation')
        self.show()
            
        self.initSquaresComputation()
        
        # Escalier au début pour faire jolie
        test = []
        for i in range(0,numSpectrumBands):
            test.append(i/numSpectrumBands)
        self.setSpectrum(test)
     
    ####################################
    ###    Gui Read Audio Button     ###
    ####################################
     
    def readAudio(self, pressed):
        
        # source = self.sender()
        fileAudioPath = self.openFile()
        # fileAudioPath = "D:/Music/Nablast/TestLeds2.wav"
        Thread(None,processAudio,args=(self,fileAudioPath)).start()
    
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', 'D:\DevProjects\LED\RaspberryPi\FromSoundToLED\data', 'AudioFile (*.wav)')
        return fileName
        
    ###########################
    ###    Gui Spectrum     ###
    ###########################
    
    def changeSpectrum(self,values):
        thread = changeSpectrumThread(values)
        self.connect(thread, QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.setSpectrum)
        thread.start()
        
    def setSpectrum(self,values):
        
        for i,v in enumerate(values):
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, int(self.hSpectrum + ratioSizeSquare*3*sizeWindows*(1-v)), ratioLines*sizeWindows, int(ratioSizeSquare*3*sizeWindows - ratioSizeSquare*3*sizeWindows*(1-v)))
            
        self.setSquares(values)
        
    def setMinAndMaxOnSpectrum(self):
        
        # Pour chaque bande de spectre
        for i in range(0,numSpectrumBands):
            
            #Pour chaque Led
            for iLed in range(ledNumber):
                if (self.buttonsForSquare[iLed][i].isChecked()):
                
                    self.guiTreasholdLMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2 - 3, int(self.hSpectrum + ratioSizeSquare*3*sizeWindows*(1-self.min[iLed])), ratioLines*sizeWindows, 3 )
                    self.guiTreasholdLMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2 - 3, int(self.hSpectrum + ratioSizeSquare*3*sizeWindows*(1-self.max[iLed])), ratioLines*sizeWindows, 3 )
                    
                else:
                    self.guiTreasholdLMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, 0, ratioLines*sizeWindows, 0 )
                    self.guiTreasholdLMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, 0, ratioLines*sizeWindows, 0 )
        
    ##########################
    ###      Gui LEDS      ###
    ##########################
        
    def changeSquares(self,values):
        thread = changeSquaresThread(values)
        self.connect(thread, QtCore.SIGNAL("setSquares(PyQt_PyObject)"), self.setSquares)
        thread.start()
        
    def setSquares(self,values):
    
        valuesForEachSquares = self.computeSquareValues(values)
        
        self.setMinAndMaxOnSpectrum()
        
        self.colRed.setRed(valuesForEachSquares[0]*255)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colGreen.setGreen(valuesForEachSquares[1]*255)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
        self.colBlue.setBlue(valuesForEachSquares[2]*255)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
        
    def initSquaresComputation(self):
        
        self.min = [1] * ledNumber
        self.max = [0] * ledNumber
        
    def computeSquareValues(self,values):
    
        self.maxChanged = [False]*ledNumber
        self.minChanged = [False]*ledNumber
        
        result = []
       
        # Process for each led
        for iLed in range(ledNumber):
        
            currentMax = 0
            # For each Led : get max and min on values checked by buttons
            for i,v in enumerate(values):
                if (self.buttonsForSquare[iLed][i].isChecked()):
                    if (v > self.max[iLed]):
                        self.max[iLed] = v
                        self.maxChanged[iLed] = True
                    elif (v < self.min[iLed]):
                        self.min[iLed] = v
                        self.minChanged[iLed] = True
                        
                    if (v > currentMax):
                        currentMax = v
                       
            # Define lower and uppert threash in terms of min and max
            cThreshL = self.min[iLed] + threashL[iLed]
            cThreshU = self.max[iLed] - threashU[iLed]
            
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
                
       
# Convert the audio data to numbers, num_samples at a time.
def read_audio(audio_stream_input, audio_stream_output, num_samples,sound, wf):
    while sound != b'':
        audio_stream_output.write(sound)
        # Read all the input data. 
        # samples = audio_stream_input.read(num_samples) 
        # Convert input data to numbers
        samplesNp = np.fromstring(sound, dtype=np.int16).astype(np.float)
        samples_l = samplesNp[::2]  
        samples_r = samplesNp[1::2]
        sound = wf.readframes(num_samples)
        yield (samples_l, samples_r)
        
# Convert the audio data to numbers, num_samples at a time.
def read_audio_Original(audio_stream_input, audio_stream_output, num_samples,sound, wf):
    while True:
        audio_stream_output.write(sound)
        # Read all the input data. 
        samples = audio_stream_input.read(num_samples) 
        # Convert input data to numbers
        samples = np.fromstring(samples, dtype=np.int16).astype(np.float)
        samples_l = samples[::2]  
        samples_r = samples[1::2]
        sound = wf.readframes(num_samples)
        yield (samples_l, samples_r) 
        
def processAudio(guiObj,fileAudioPath):

    ComputeOriginal = True

    wf = wave.open(fileAudioPath, 'rb')
    
    rate = wf.getframerate()
    
    p=pyaudio.PyAudio()
    audio_stream_input =p.open(format=p.get_format_from_width(wf.getsampwidth()),\
                                channels=wf.getnchannels(),\
                                rate = rate,\
                                input=True,\
                                frames_per_buffer=CHUNK)\
                                
    audio_stream_output =p.open(format=p.get_format_from_width(wf.getsampwidth()),\
                                channels=wf.getnchannels(),\
                                rate = rate,\
                                output=True,\
                                frames_per_buffer=CHUNK)\
                  
    print("Reading Audio File at :" + fileAudioPath + " with rate : " + str(rate))
    
    sound = wf.readframes(CHUNK)

    audio = read_audio(audio_stream_input,audio_stream_output, num_samples=CHUNK, sound=sound, wf=wf)
    
    spectrumGen = notes_scaled_nosaturation_Original.process(audio,\
                                            num_leds=numSpectrumBands,\
                                            num_samples=CHUNK,\
                                            sample_rate=rate)
                                                
    
    # for sample, led in zip(audio,leds):
    count = 0
    for spectrum in spectrumGen:
        # Spectrum
        guiObj.changeSpectrum(spectrum[0:numSpectrumBands])
        
        ledValues, min, max = computeLedValues(spectrum)
        
        guiObj.changeMinAndMax(min,max)
        guiObj.changeSquareThread(ledValues)
        
        
        
    
    
        
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = MyFirstGUI()
    sys.exit(app.exec_())
    