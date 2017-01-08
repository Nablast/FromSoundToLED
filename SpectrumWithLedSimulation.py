import sys
from PyQt4 import QtGui, QtCore
import pdb

import pyaudio
import numpy as np
import pylab
import time
import wave
import matplotlib.pyplot as plt
from threading import Thread
from colorsys import hls_to_rgb

import notes_scaled_nosaturation

CHUNK = 256

sizeWindows = 800
ratioSizeSquare = 0.15

ratioLines = 0.01
spaceBetweenLines = 0.005

numSpectrumBands = 30

smoothness = 70

threashold1 = 0.85
threashold2 = 0.5
threashold3 = 0.5
            
class changeSquareThread(QtCore.QThread):

    def __init__(self, ledId, value):
        QtCore.QThread.__init__(self)
        self.ledId = ledId
        self.value = value

    def __del__(self):
        self.wait()

    def run(self):
        if self.ledId == 0:
            self.emit(QtCore.SIGNAL("setRed(int)"), self.value)
        elif self.ledId == 1:
            self.emit(QtCore.SIGNAL("setGreen(int)"), self.value)
        elif self.ledId == 2:
            self.emit(QtCore.SIGNAL("setBlue(int)"), self.value)
            
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
        self.initUI()
        
    def initUI(self):      

        but = QtGui.QPushButton('Read Audio', self)
        but.setCheckable(True)
        but.resize(0.2*sizeWindows,0.05*sizeWindows)
        h = sizeWindows*(1/10) - 0.05*sizeWindows/2
        w = sizeWindows*(1/2) - 0.2*sizeWindows/2
        but.move(w, h)
        but.clicked[bool].connect(self.readAudio)
    
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette)
        
        self.col = QtGui.QColor(0, 0, 0)   

        hSquares = sizeWindows*(5/6)
        
        # Squares Led
        self.colRed = QtGui.QColor(255, 0, 0)   
        self.squareRed = QtGui.QFrame(self)
        self.squareRed.setGeometry(sizeWindows*(1/4) - ratioSizeSquare*sizeWindows/2, hSquares - ratioSizeSquare*sizeWindows/2, ratioSizeSquare*sizeWindows, ratioSizeSquare*sizeWindows)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colGreen = QtGui.QColor(0, 255, 0)   
        self.squareGreen = QtGui.QFrame(self)
        self.squareGreen.setGeometry(sizeWindows*(2/4) - ratioSizeSquare*sizeWindows/2, hSquares - ratioSizeSquare*sizeWindows/2, ratioSizeSquare*sizeWindows, ratioSizeSquare*sizeWindows)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
        self.colBlue = QtGui.QColor(0, 0, 255)   
        self.squareBlue = QtGui.QFrame(self)
        self.squareBlue.setGeometry(sizeWindows*(3/4) - ratioSizeSquare*sizeWindows/2, hSquares - ratioSizeSquare*sizeWindows/2, ratioSizeSquare*sizeWindows, ratioSizeSquare*sizeWindows)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
        
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
        
        # Buttons
        self.buttonsForSquare1 = []
        self.buttonsForSquare2 = []
        self.buttonsForSquare3 = []
        self.hButtons1 = self.hSpec + ratioSizeSquare*sizeWindows/2 + spaceBetweenLines*sizeWindows
        self.hButtons2 = self.hButtons1 + spaceBetweenLines*sizeWindows + ratioLines*sizeWindows
        self.hButtons3 = self.hButtons2 + spaceBetweenLines*sizeWindows + ratioLines*sizeWindows
        for i in range(0,numSpectrumBands):
            self.buttonsForSquare1.append(QtGui.QCheckBox("",self))
            self.buttonsForSquare1[i].resize(ratioLines*sizeWindows,ratioLines*sizeWindows)
            self.buttonsForSquare1[i].move(self.wSpectrum[i]-ratioLines*sizeWindows/2, self.hButtons1 + ratioLines*sizeWindows/2)
            
            self.buttonsForSquare2.append(QtGui.QCheckBox("",self))
            self.buttonsForSquare2[i].resize(ratioLines*sizeWindows,ratioLines*sizeWindows)
            self.buttonsForSquare2[i].move(self.wSpectrum[i]-ratioLines*sizeWindows/2, self.hButtons2 + ratioLines*sizeWindows/2)
            
            self.buttonsForSquare3.append(QtGui.QCheckBox("",self))
            self.buttonsForSquare3[i].resize(ratioLines*sizeWindows,ratioLines*sizeWindows)
            self.buttonsForSquare3[i].move(self.wSpectrum[i]-ratioLines*sizeWindows/2, self.hButtons3 + ratioLines*sizeWindows/2)
            
            
        self.setWindowTitle('LED Simulation')
        self.show()
        
        # Init max
        maxBand = []
        for i in range(0,numSpectrumBands):
            maxBand.append(0)
        
        # Escalier au début pour faire jolie
        test = []
        for i in range(0,numSpectrumBands):
            test.append(i/numSpectrumBands)
        self.setSpectrum(test)
        
    def readAudio(self, pressed):
        
        # source = self.sender()
        fileAudioPath = self.openFile()
        # fileAudioPath = "D:/Music/Nablast/TestLeds2.wav"
        Thread(None,processAudio,args=(self,fileAudioPath)).start()
        
    def setSpectrum(self,values):
        for i,v in enumerate(values):
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, int(self.hSpectrum + ratioSizeSquare*3*sizeWindows*(1-v)), ratioLines*sizeWindows, int(ratioSizeSquare*3*sizeWindows - ratioSizeSquare*3*sizeWindows*(1-v)))
    
        self.setSquares(values)
    
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', '', 'AudioFile (*.wav)')
        return fileName
        
    def changeSpectrum(self,values):
        thread = changeSpectrumThread(values)
        self.connect(thread, QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.setSpectrum)
        thread.start()
        
    def setSquares(self,values):
    
        valueFor1 = 0
        valueFor2 = 0
        valueFor3 = 0
        
        for i,v in enumerate(values):
        
            if (self.buttonsForSquare1[i].isChecked() and valueFor1 < v):
                valueFor1 = v
            
            if (self.buttonsForSquare2[i].isChecked() and valueFor2 < v):
                valueFor2 = v
                
            if (self.buttonsForSquare3[i].isChecked() and valueFor3 < v):
                valueFor3 = v
                
        if valueFor1 < threashold1:
            valueFor1 = 0
        
        if valueFor2 < threashold2:
            valueFor2 = 0
        
        if valueFor3 < threashold3:
            valueFor3 = 0
        
        self.colRed.setRed(valueFor1*255)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colGreen.setGreen(valueFor2*255)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
        self.colBlue.setBlue(valueFor3*255)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
       
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
        sound = wf.readframes(512)
        yield (samples_l, samples_r)
        
def lum_hue(leds, num_leds):
	for samples in leds:
		sum_for_hue = 0
		for i, v in enumerate(samples):
			sum_for_hue += i * v

		lum = sum(samples) / float(len(samples))
		hue = sum_for_hue / float(sum(samples) or 1) / float(len(samples))

		yield (hue, lum)
		
def rolling_scale(vals, falloff):
	v_min = None
	v_max = None
	for val in vals:
		if v_min is None:
			v_min = val
			v_max = val
		else:
			v_min = tuple(map(min, zip(v_min, val)))
			v_max = tuple(map(max, zip(v_max, val)))
		v_min = tuple(i * falloff + j * (1 - falloff) for i, j in zip(v_min, val))
		v_max = tuple(i * falloff + j * (1 - falloff) for i, j in zip(v_max, val))
		if v_max != v_min:
			yield tuple((vc - vmin) / float(vmax - vmin) for vc, vmin, vmax in zip(val, v_min, v_max))
		else:
			yield val

def colorize(hlgen):
	hlgen = rolling_scale(hlgen, 0.999)

	for hue, lum in hlgen:
		yield hls_to_rgb(hue, lum, 1)
        
def processAudio(guiObj,fileAudioPath):

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

    audio = read_audio(audio_stream_input,audio_stream_output, num_samples=CHUNK,sound=sound, wf=wf)
    
    leds = notes_scaled_nosaturation.process(audio,\
                                                num_leds=numSpectrumBands,\
                                                num_samples=CHUNK,\
                                                sample_rate=rate,\
                                                falloff_val=smoothness/100.0)
    
    # for sample, led in zip(audio,leds):
    for led in leds:

        # Spectrum
        guiObj.changeSpectrum(led[0:numSpectrumBands])
    
        
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = MyFirstGUI()
    sys.exit(app.exec_())
    