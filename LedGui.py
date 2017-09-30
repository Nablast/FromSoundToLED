import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QPainter
import pdb

import numpy as np
import math
import pyaudio
import wave
from threading import Thread

#Test
import matplotlib.pyplot as plt

SampleRate = 22050
CHUNK = 1024

sizeWindows = 1000
numSpectrumBands = 128
nbLeds = 4

frequencySeparators = [[0,70], \
                       [300, 600], \
                       [600,1100], \
                       [3000,3500]]

ratioSizeSquareMax = 0.15
ratioLines = 0.0035
spaceBetweenLines = 0.0025

from LedsValuesComputation import LedsValuesComputation

Smoothness = [0.95,0.95,0.95,0.95]

ThreashL = [0.3,0.3,0.15,0.15]
ThreashU = [0.2,0.4,0.4,0.3]

global stopAudio
stopAudio = False

class changeLedsThread(QtCore.QThread):

    def __init__(self, values):
        QtCore.QThread.__init__(self)
        self.values = values

    def __del__(self):
        self.wait()

    def run(self):
        self.emit(QtCore.SIGNAL("setLeds(PyQt_PyObject)"), self.values)
            
class changeSpectrumThread(QtCore.QThread):

    def __init__(self, values):
        QtCore.QThread.__init__(self)
        self.values = values

    def __del__(self):
        self.wait()
        
    def run(self):
        self.emit(QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.values)
        
class changeMinAndMaxOnSpectrumThread(QtCore.QThread):

    def __init__(self, valuesMax, valuesMin, threashL, threashH):
        QtCore.QThread.__init__(self)
        self.valuesMax = valuesMax
        self.valuesMin = valuesMin
        
        self.threashL = threashL
        self.threashH = threashH

    def __del__(self):
        self.wait()
        
    def run(self):
        self.emit(QtCore.SIGNAL("setMinAndMaxOnSpectrum(PyQt_PyObject)"), [self.valuesMax, self.valuesMin, self.threashL, self.threashH])

class LedGUI(QtGui.QWidget):

    def __init__(self, sizeWindows, numSpectrumBands, nbLeds):
    
        self.ledCurrentValues = [0]*nbLeds
    
        super(LedGUI, self).__init__()
        self.resize(sizeWindows, sizeWindows)
        
        self.sizeWindows = sizeWindows
        self.numSpectrumBands = numSpectrumBands
        self.nbLeds = nbLeds
        
        # Background
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette) 
        
        # Initialisations
        self.initReadAudioButton()
        self.initLEDs()
        self.initSpectrum()
        
        self.setWindowTitle('LED Simulation')
        self.show()
        
    def closeEvent(self, evnt):
        global stopAudio
        stopAudio = True
        super(LedGUI, self).closeEvent(evnt)
        
    # Used to paint LEDs
    def paintEvent(self, e):
    
        painter = QPainter()
        painter.begin(self)
        
        for i in range(nbLeds):
        
            grad = QtGui.QRadialGradient(QtCore.QPointF(self.ledsRect[i].center()), 70.0)
            grad.setColorAt(0, QtGui.QColor(self.ledCurrentValues[i]*self.ledColors[i][0], self.ledCurrentValues[i]*self.ledColors[i][1], self.ledCurrentValues[i]*self.ledColors[i][2]))
            grad.setColorAt(1, QtCore.Qt.black)
            painter.setBrush(grad)
            painter.drawEllipse(self.ledsRect[i])
        
        painter.end()
        
    def initReadAudioButton(self):
    
        # Button Read Audio
        but = QtGui.QPushButton('Read Local Sound', self)
        but.setCheckable(True)
        but.resize(0.2*self.sizeWindows,0.05*self.sizeWindows)
        h = self.sizeWindows*(1/10) - 0.05*self.sizeWindows/2
        w = self.sizeWindows*(1/4) - 0.2*self.sizeWindows/2
        but.move(w, h)
        but.clicked[bool].connect(self.processAudioLocal)

        but2 = QtGui.QPushButton('Read Micro Input', self)
        but2.setCheckable(True)
        but2.resize(0.2*self.sizeWindows,0.05*self.sizeWindows)
        h = self.sizeWindows*(1/10) - 0.05*self.sizeWindows/2
        w = self.sizeWindows*(3/4) - 0.2*self.sizeWindows/2
        but2.move(w, h)
        but2.clicked[bool].connect(self.processAudioMicro)
        
    def initLEDs(self):
    
        self.ledsRect = []
        

        
        squareSize = min(ratioSizeSquareMax*self.sizeWindows, 4 * self.sizeWindows / ((5*self.nbLeds)+1))
        hSquares = self.sizeWindows*(5/6)
        for iLed in range(self.nbLeds):
            self.ledsRect.append(QtCore.QRect(self.sizeWindows*((iLed+1)/(self.nbLeds+1)) - squareSize/2, hSquares - squareSize/2, squareSize, squareSize))
         
    def initSpectrum(self):
    
        # xSpectrum = np.array([float(SampleRate)*float(i)/float(CHUNK) for i in range(int(CHUNK/2))])
        # ySpectrum = np.array(range(int(CHUNK/2)))
        
        # plt.ion()

        # self.figTest = plt.figure()
        # ax = self.figTest.add_subplot(111)
        # self.lineTest, = ax.plot(xSpectrum, ySpectrum, 'r-') # Returns a tuple of line objects, thus the comma
        # ax.axis([xSpectrum[0], xSpectrum[-1], 0, 1])
        # self.figTest.canvas.draw()
    
        # Define led by Bins
        frequencies = [SampleRate*i/CHUNK for i in range(1,int(CHUNK/2)+1)]
        self.ledByBins = [-1]*int(CHUNK/2)
        for indexBin in range(int(CHUNK/2)):
            currentFreq = frequencies[indexBin]
            for iLed in range(len(frequencySeparators)):
                if currentFreq >= frequencySeparators[iLed][0] and currentFreq < frequencySeparators[iLed][1]:
                    self.ledByBins[indexBin] = iLed
                    
        # Spectrum
        self.spectrumLines = []
        self.wSpectrum = []
        self.ySpectrum = self.sizeWindows*(1/2)
        self.heightSpectrumMax = self.sizeWindows*(1/4)
        for i in range(0,self.numSpectrumBands):

            self.spectrumLines.append(QtGui.QFrame(self))
            self.wSpectrum.append(self.sizeWindows*(1/2) + (i - self.numSpectrumBands/2)*(ratioLines+spaceBetweenLines)*self.sizeWindows)
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, self.ySpectrum, ratioLines*self.sizeWindows, 0 )
            
            # Line Color
            if self.ledByBins[i] != -1:
                r,g,b = self.ledColors[self.ledByBins[i]]
            else:
                r,g,b = [255,255,255]
            self.spectrumLines[i].setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(r, g, b).name())
        
        # Min and Max on GUI
        self.heightMinMaxFrame = ratioLines*self.sizeWindows*0.2
        self.guiMin = []
        self.guiMax = []
        self.guiThreashLow = []
        self.guiThreashHigh = []
        for i in range(0,self.numSpectrumBands):
            self.guiMin.append([])
            self.guiMax.append([])
            self.guiThreashLow.append([])
            self.guiThreashHigh.append([])
            for iLed in range(self.nbLeds):

                colorLed = QtGui.QColor(self.ledColors[iLed][0],self.ledColors[iLed][1],self.ledColors[iLed][2])
                colorLed2 = QtGui.QColor(self.ledColors[iLed][0] - 0.2,self.ledColors[iLed][1] - 0.2,self.ledColors[iLed][2] - 0.2)

                self.guiMin[i].append(QtGui.QFrame(self))
                self.guiMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                self.guiMin[i][iLed].setStyleSheet("QWidget { background-color: %s }" % colorLed.name())
                
                self.guiMax[i].append(QtGui.QFrame(self))
                self.guiMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                self.guiMax[i][iLed].setStyleSheet("QWidget { background-color: %s }" % colorLed.name())
                
                self.guiThreashLow[i].append(QtGui.QFrame(self))
                self.guiThreashLow[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                self.guiThreashLow[i][iLed].setStyleSheet("QWidget { background-color: %s }" % colorLed2.name())
                
                self.guiThreashHigh[i].append(QtGui.QFrame(self))
                self.guiThreashHigh[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                self.guiThreashHigh[i][iLed].setStyleSheet("QWidget { background-color: %s }" % colorLed2.name())
                
        # Escalier au début pour faire jolie
        test = []
        for i in range(0,self.numSpectrumBands):
            test.append(i/self.numSpectrumBands)
        self.setSpectrum(test)
        
    ##########################
    ###      Gui LEDS      ###
    ##########################  
        
    def changeLeds(self,values):
        thread = changeLedsThread(values)
        self.connect(thread, QtCore.SIGNAL("setLeds(PyQt_PyObject)"), self.setLeds)
        thread.start()
        
    def setLeds(self,valuesForEachLed):
        
        self.ledCurrentValues = valuesForEachLed
        self.update()
        
        
    ###########################
    ###    Gui Spectrum     ###
    ###########################
    
    def changeSpectrum(self,values):
        thread = changeSpectrumThread(values)
        self.connect(thread, QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.setSpectrum)
        thread.start()
        
    def setSpectrum(self,values):
       
        for i in range(numSpectrumBands):
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, int(self.ySpectrum - self.heightSpectrumMax * values[i]), ratioLines*sizeWindows, int(self.heightSpectrumMax*values[i]))
        
    def changeMinAndMaxOnSpectrum(self,valuesMax,valuesMin, threashL, threashH):
        thread = changeMinAndMaxOnSpectrumThread(valuesMax,valuesMin, threashL, threashH)
        self.connect(thread, QtCore.SIGNAL("setMinAndMaxOnSpectrum(PyQt_PyObject)"), self.setMinAndMaxOnSpectrum)
        thread.start()
        
    def setMinAndMaxOnSpectrum(self,valuesMaxMinThreshLU):
        
        valuesMax = valuesMaxMinThreshLU[0]
        valuesMin = valuesMaxMinThreshLU[1]
        threashLow = valuesMaxMinThreshLU[2]
        threashHigh = valuesMaxMinThreshLU[3]
        
        # Pour chaque bande de spectre
        for i in range(0,self.numSpectrumBands):
            
            #Pour chaque Led
            for iLed in range(self.nbLeds):
                if (self.ledByBins[i] == iLed):
                    
                    self.guiMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, int(self.ySpectrum - self.heightSpectrumMax*valuesMin[iLed]), ratioLines*sizeWindows, 3 )
                    self.guiMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, int(self.ySpectrum - self.heightSpectrumMax*valuesMax[iLed]), ratioLines*sizeWindows, 3 )
                    
                    self.guiThreashLow[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, int(self.ySpectrum - self.heightSpectrumMax*threashLow[iLed]), ratioLines*sizeWindows, 3 )
                    self.guiThreashHigh[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, int(self.ySpectrum - self.heightSpectrumMax*threashHigh[iLed]), ratioLines*sizeWindows, 3 )
     
    ####################################
    ###    Gui Read Audio Button     ###
    ####################################
    
    # Convert the audio data to numbers, num_samples at a time.
    def read_audio(self, audio_stream_input, audio_stream_output, num_samples,sound, wf, ):
        global stopAudio
        while sound != b'' and not (stopAudio):
            audio_stream_output.write(sound)
            # Read all the input data. 
            # samples = audio_stream_input.read(num_samples) 
            # Convert input data to numbers
            samplesNp = np.fromstring(sound, dtype=np.int16).astype(np.float)
            samples_l = samplesNp[::2]  
            samples_r = samplesNp[1::2]
            sound = wf.readframes(num_samples)
                 
            yield (samples_l, samples_r)
            
        if not (stopAudio):
            print('Sound stop')


    def read_micro(self, audio_stream_input, audio_stream_output, num_samples):
    
        while 1:
            
            # Read all the input data. 
            samples = audio_stream_input.read(num_samples) 
            # Convert input data to numbers
            samplesNp = np.fromstring(samples, dtype=np.int16).astype(np.float)
            samples_l = samplesNp[::2]  
            samples_r = samplesNp[1::2]
            audio_stream_output.write(samples)
                 
            yield (samples_l, samples_r)
     
    def processAudioImpl(GuiObject, fileAudioPath,LocalFile):

        try:
            p=pyaudio.PyAudio()
            
            if LocalFile:

                wf = wave.open(fileAudioPath, 'rb')
                TestSampleRate = wf.getframerate()
                p=pyaudio.PyAudio()
                
                # Reading Sound at SampleRate : SampleRate

                LedsComputator = LedsValuesComputation(SampleRate, CHUNK, frequencySeparators,  ThreashL, ThreashU)

                audio_stream_input =p.open(format=p.get_format_from_width(wf.getsampwidth()),\
                                            channels=wf.getnchannels(),\
                                            rate = SampleRate,\
                                            input=True,\
                                            frames_per_buffer=CHUNK)\
                                            
                audio_stream_output =p.open(format=p.get_format_from_width(wf.getsampwidth()),\
                                            channels=wf.getnchannels(),\
                                            rate = TestSampleRate,\
                                            output=True,\
                                            frames_per_buffer=CHUNK)\

                sound = wf.readframes(CHUNK)

                audio = GuiObject.read_audio(audio_stream_input,audio_stream_output, CHUNK, sound, wf)

            else:

                LedsComputator = LedsValuesComputation(SampleRate, CHUNK, frequencySeparators, ThreashL, ThreashU)

                audio_stream_input = p.open(format=pyaudio.paInt16,\
                                            channels=2,\
                                            rate=SampleRate,\
                                            input=True,\
                                            frames_per_buffer=CHUNK)\

                audio_stream_output =p.open(format=pyaudio.paInt16,\
                                            channels=2,\
                                            rate = SampleRate,\
                                            output=True,\
                                            frames_per_buffer=CHUNK)\

                audio = GuiObject.read_micro(audio_stream_input,audio_stream_output, CHUNK)          
                
            valuesGen = LedsComputator.process(audio)

            lastValues = [0]*nbLeds
            for spectrum, ledsValues, max, min, threashL, threashH, maxAudioSample in valuesGen:
                
                # Do not light up Leds if there is no sound.
                if (maxAudioSample < 10):
                    ledsValues = [0 for i in range(len(ledsValues))]
            
                # Smooth Leds
                for i in range(nbLeds):
                    if ledsValues[i] < lastValues[i]:
                        ledsValues[i] = ledsValues[i] + (lastValues[i] - ledsValues[i]) * Smoothness[i]
                
                lastValues = ledsValues
                
                GuiObject.changeSpectrum(spectrum)
                GuiObject.changeLeds(ledsValues)
                GuiObject.changeMinAndMaxOnSpectrum(max,min, threashL, threashH)
                
        except Exception as e:
            GuiObject.close()
            raise(e)
    
    def processAudioLocal(self, pressed):
        
        fileAudioPath = self.openFile()
        Thread(None,LedGUI.processAudioImpl,args=(self,fileAudioPath,True)).start()

    def processAudioMicro(self, pressed):
        
        Thread(None,LedGUI.processAudioImpl,args=(self,'',False)).start()
    
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', 'D://DevProjects//FromSoundToLED//data', 'AudioFile (*.wav)')
        return fileName
        
       
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = LedGUI(sizeWindows, numSpectrumBands, nbLeds)
    sys.exit(app.exec_())
    ex.stopMe()