import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QPainter
import pdb

import numpy as np
import math
import pyaudio
import wave
from threading import Thread

CHUNK = 1024

sizeWindows = 800
numSpectrumBands = 64
nbLeds = 3

ratioSizeSquareMax = 0.15
ratioLines = 0.01
spaceBetweenLines = 0.005

from LedsValuesComputation import LedsValuesComputation

buttonsBool = np.array([[1],[i for i in range(8,24)],[i for i in range(27,63)]])

Smoothness = [0.6,0.5,0.85]

ThreashL = [0.3,0.3,0.05]
ThreashU = [0.2,0.1,0.3]

def HueToRgb(H):
    
    # Hue = HSL
    # H = rotation
    # S = Saturation (=1)
    # L = Luminance (=1)
    S = 1.
    L = 0.5 
    
    if L < 0.5:
        temp1 = L * (1.0 + S)
    else:
        temp1 = S + L - L*S  
    
    temp2 = 2.0*L - temp1
    
    print('T2 = ' + str(temp2)) 
    
    tempR = H + 1.0/3.0
    if tempR > 1.0:
        tempR = tempR - 1.0

    tempG = H
    tempB = H - 1.0/3.0
    if tempB < 0.0:
        tempB = tempB + 1.0     
    
    if 6.0*tempR < 1.0:
        r = temp2 + (temp1 - temp2) * 6.0 * tempR
    elif 2.0*tempR < 1.0:
        r = temp1
    elif 3.0*tempR < 2.0:
        r = temp2 + (temp1 - temp2) * (2.0/3.0 - tempR)* 6.0
    else:
        r = temp2
    
    if 6.0*tempG < 1.0:
        g = temp2 + (temp1 - temp2) * 6.0 * tempG
    elif 2.0*tempG < 1.0:
        g = temp1
    elif 3.0*tempG < 2.0:
        g = temp2 + (temp1 - temp2) * (2.0/3.0 - tempG)* 6.0
    else:
        g = temp2

    if 6.0*tempB < 1.0:
        b = temp2 + (temp1 - temp2) * 6.0 * tempB
    elif 2.0*tempB < 1.0:
        b = temp1
    elif 3.0*tempB < 2.0:
        b = temp2 + (temp1 - temp2) * (2.0/3.0 - tempB)* 6.0
    else:
        b = temp2            
    
    return int(r*255), int(g*255), int(b*255)

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

    def __init__(self, valuesMax, valuesMin):
        QtCore.QThread.__init__(self)
        self.valuesMax = valuesMax
        self.valuesMin = valuesMin

    def __del__(self):
        self.wait()
        
    def run(self):
        self.emit(QtCore.SIGNAL("setMinAndMaxOnSpectrum(PyQt_PyObject)"), [self.valuesMax, self.valuesMin])

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
        
        self.ledColors = []
        for iLed in range(self.nbLeds):
            Hue = iLed*360/self.nbLeds
            r,g,b = HueToRgb(Hue/360.0)
            self.ledColors.append([r,g,b])
        
        squareSize = min(ratioSizeSquareMax*self.sizeWindows, 4 * self.sizeWindows / ((5*self.nbLeds)+1))
        hSquares = self.sizeWindows*(5/6)
        for iLed in range(self.nbLeds):
            self.ledsRect.append(QtCore.QRect(self.sizeWindows*((iLed+1)/(self.nbLeds+1)) - squareSize/2, hSquares - squareSize/2, squareSize, squareSize))
         
    def initSpectrum(self):
    
        # Spectrum
        self.spectrumLines = []
        self.wSpectrum = []
        self.ySpectrum = self.sizeWindows*(1/2)
        self.heightSpectrumMax = self.sizeWindows*(1/4)
        for i in range(0,self.numSpectrumBands):
            self.spectrumLines.append(QtGui.QFrame(self))
            self.wSpectrum.append(self.sizeWindows*(1/2) + (i - self.numSpectrumBands/2)*(ratioLines+spaceBetweenLines)*self.sizeWindows)
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, self.ySpectrum, ratioLines*self.sizeWindows, 0 )
            self.spectrumLines[i].setStyleSheet("QWidget { background-color: %s }" % QtGui.QColor(255, 255, 255).name())
            
        # Buttons Below Spectrums
        self.buttonsForSquare = [[]] * self.nbLeds
        hButtons = self.ySpectrum
        for iLed in range(self.nbLeds):
            hButtons = hButtons + spaceBetweenLines*self.sizeWindows + ratioLines*self.sizeWindows
            self.buttonsForSquare[iLed] = [None]*self.numSpectrumBands
            for i in range(self.numSpectrumBands):
                self.buttonsForSquare[iLed][i] = QtGui.QCheckBox("",self)
                self.buttonsForSquare[iLed][i].resize(ratioLines*self.sizeWindows,ratioLines*self.sizeWindows)
                self.buttonsForSquare[iLed][i].move(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, hButtons + ratioLines*self.sizeWindows/2)  

                if (i in buttonsBool[iLed]):    
                    self.buttonsForSquare[iLed][i].setChecked(True)
        
        # Min and Max on GUI
        self.heightMinMaxFrame = ratioLines*self.sizeWindows*0.2
        self.guiTreasholdLMin = []
        self.guiTreasholdLMax = []
        for i in range(0,self.numSpectrumBands):
            self.guiTreasholdLMin.append([])
            self.guiTreasholdLMax.append([])
            for iLed in range(self.nbLeds):

                colorLed = QtGui.QColor(self.ledColors[iLed][0],self.ledColors[iLed][1],self.ledColors[iLed][2])

                self.guiTreasholdLMin[i].append(QtGui.QFrame(self))
                self.guiTreasholdLMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                self.guiTreasholdLMin[i][iLed].setStyleSheet("QWidget { background-color: %s }" % colorLed.name())
                
                self.guiTreasholdLMax[i].append(QtGui.QFrame(self))
                self.guiTreasholdLMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                self.guiTreasholdLMax[i][iLed].setStyleSheet("QWidget { background-color: %s }" % colorLed.name())
                
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
        
        for i,v in enumerate(values):
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, int(self.ySpectrum - self.heightSpectrumMax * v), ratioLines*sizeWindows, int(self.heightSpectrumMax*v))
        
    def changeMinAndMaxOnSpectrum(self,valuesMax,valuesMin):
        thread = changeMinAndMaxOnSpectrumThread(valuesMax,valuesMin)
        self.connect(thread, QtCore.SIGNAL("setMinAndMaxOnSpectrum(PyQt_PyObject)"), self.setMinAndMaxOnSpectrum)
        thread.start()
        
    def setMinAndMaxOnSpectrum(self,valuesMaxMin):
        
        valuesMax = valuesMaxMin[0]
        valuesMin = valuesMaxMin[1]
        
        # Pour chaque bande de spectre
        for i in range(0,self.numSpectrumBands):
            
            #Pour chaque Led
            for iLed in range(self.nbLeds):
                if (self.buttonsForSquare[iLed][i].isChecked()):
                
                    self.guiTreasholdLMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2 - 3, int(self.ySpectrum - self.heightSpectrumMax*valuesMin[iLed]), ratioLines*sizeWindows, 3 )
                    self.guiTreasholdLMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2 - 3, int(self.ySpectrum - self.heightSpectrumMax*valuesMax[iLed]), ratioLines*sizeWindows, 3 )
                    
                else:
                    self.guiTreasholdLMin[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                    self.guiTreasholdLMax[i][iLed].setGeometry(self.wSpectrum[i]-ratioLines*self.sizeWindows/2, 0, ratioLines*self.sizeWindows, 0 )
                    
    def getCurrentButtonsStates(self):
        
        currentButtonsBool = np.array([self.buttonsForSquare[iLed][i].isChecked() for iLed in range(self.nbLeds) for i in range(self.numSpectrumBands)])
        currentButtonsBool = currentButtonsBool.reshape((self.nbLeds, self.numSpectrumBands))
        
        return currentButtonsBool
     
    ####################################
    ###    Gui Read Audio Button     ###
    ####################################
    
    # Convert the audio data to numbers, num_samples at a time.
    def read_audio(self, audio_stream_input, audio_stream_output, num_samples,sound, wf):
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

        p=pyaudio.PyAudio()

        if LocalFile:

            wf = wave.open(fileAudioPath, 'rb')
            rate = wf.getframerate()
            p=pyaudio.PyAudio()

            LedsComputator = LedsValuesComputation(GuiObject.nbLeds, GuiObject.numSpectrumBands, rate, CHUNK, GuiObject.getCurrentButtonsStates(),  ThreashL, ThreashU)

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

            sound = wf.readframes(CHUNK)

            audio = GuiObject.read_audio(audio_stream_input,audio_stream_output, CHUNK, sound, wf)

        else:

            rate = 44100
            LedsComputator = LedsValuesComputation(GuiObject.nbLeds, GuiObject.numSpectrumBands, rate, CHUNK, GuiObject.getCurrentButtonsStates(), ThreashL, ThreashU)

            audio_stream_input = p.open(format=pyaudio.paInt16,\
                                        channels=2,\
                                        rate=rate,\
                                        input=True,\
                                        frames_per_buffer=CHUNK)\

            audio_stream_output =p.open(format=pyaudio.paInt16,\
                                        channels=2,\
                                        rate = rate,\
                                        output=True,\
                                        frames_per_buffer=CHUNK)\

            audio = GuiObject.read_micro(audio_stream_input,audio_stream_output, CHUNK)          
            
        valuesGen = LedsComputator.process(audio)

        lastValues = [0]*nbLeds
        for spectrum, ledsValues, max, min, maxAudioSample in valuesGen:
        
            LedsComputator.setButtonStates(GuiObject.getCurrentButtonsStates())
            
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
            GuiObject.changeMinAndMaxOnSpectrum(max,min)
    
    def processAudioLocal(self, pressed):
        
        fileAudioPath = self.openFile()
        Thread(None,LedGUI.processAudioImpl,args=(self,fileAudioPath,True)).start()

    def processAudioMicro(self, pressed):
        
        Thread(None,LedGUI.processAudioImpl,args=(self,'',False)).start()
    
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', 'D:\DevProjects\LED\RaspberryPi\FromSoundToLED\data', 'AudioFile (*.wav)')
        return fileName
        
    
       
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = LedGUI(sizeWindows, numSpectrumBands, nbLeds)
    sys.exit(app.exec_())