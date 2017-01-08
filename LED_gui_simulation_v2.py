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
from amplitude import Amplitude

import notes_scaled_nosaturation

CHUNK = 512

sizeWindows = 500
ratioSizeSquare = 0.15

smoothness = 0

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
        
class changeAmplitudeThread(QtCore.QThread):

    def __init__(self, lr, value):
        QtCore.QThread.__init__(self)
        self.lr = lr
        self.value = value

    def __del__(self):
        self.wait()
        
    def run(self):
        if self.lr == 0:
            self.emit(QtCore.SIGNAL("setAmplitudeL(float)"), self.value)
        elif self.lr == 1:
            self.emit(QtCore.SIGNAL("setAmplitudeR(float)"), self.value)
     
class MyFirstGUI(QtGui.QWidget):

    def __init__(self):
        super(MyFirstGUI, self).__init__()
        self.resize(sizeWindows, sizeWindows)
        self.initUI()
        
    def initUI(self):      

        but = QtGui.QPushButton('Read Audio', self)
        but.setCheckable(True)
        but.resize(0.2*sizeWindows,0.05*sizeWindows)
        h = sizeWindows*(1/3) - 0.05*sizeWindows/2
        w = sizeWindows*(3/5) - 0.2*sizeWindows/2
        but.move(w, h)
        but.clicked[bool].connect(self.readAudio)
    
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette)
        
        self.col = QtGui.QColor(0, 0, 0)   
    
        self.colRed = QtGui.QColor(255, 0, 0)   
        self.squareRed = QtGui.QFrame(self)
        h = sizeWindows*(2/3) - ratioSizeSquare*sizeWindows/2
        w = sizeWindows*(2/5) - ratioSizeSquare*sizeWindows/2
        self.squareRed.setGeometry(w, h, ratioSizeSquare*sizeWindows, ratioSizeSquare*sizeWindows)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colGreen = QtGui.QColor(0, 255, 0)   
        self.squareGreen = QtGui.QFrame(self)
        h = sizeWindows*(2/3) - ratioSizeSquare*sizeWindows/2
        w = sizeWindows*(3/5) - ratioSizeSquare*sizeWindows/2
        self.squareGreen.setGeometry(w, h, ratioSizeSquare*sizeWindows, ratioSizeSquare*sizeWindows)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
        self.colBlue = QtGui.QColor(0, 0, 255)   
        self.squareBlue = QtGui.QFrame(self)
        h = sizeWindows*(2/3) - ratioSizeSquare*sizeWindows/2
        w = sizeWindows*(4/5) - ratioSizeSquare*sizeWindows/2
        self.squareBlue.setGeometry(w, h, ratioSizeSquare*sizeWindows, ratioSizeSquare*sizeWindows)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
        
        self.colWhite = QtGui.QColor(255, 255, 255)   
        self.vuMeterL = QtGui.QFrame(self)
        self.vuMeterR = QtGui.QFrame(self)
        self.hVuMeter = sizeWindows*(2/3) - ratioSizeSquare*5*sizeWindows/2
        self.wvuMeterL = sizeWindows*(1/5) - (ratioSizeSquare/4)*sizeWindows - (ratioSizeSquare/80)*sizeWindows
        self.wvuMeterR = sizeWindows*(1/5) + (ratioSizeSquare/80)*sizeWindows
        self.vuMeterL.setGeometry(self.wvuMeterL, self.hVuMeter, (ratioSizeSquare/4)*sizeWindows, ratioSizeSquare*3*sizeWindows)
        self.vuMeterR.setGeometry(self.wvuMeterR, self.hVuMeter, (ratioSizeSquare/4)*sizeWindows, ratioSizeSquare*3*sizeWindows)
        self.vuMeterL.setStyleSheet("QWidget { background-color: %s }" % self.colWhite.name())
        self.vuMeterR.setStyleSheet("QWidget { background-color: %s }" % self.colWhite.name())
        
        self.setWindowTitle('LED Simulation')
        self.show()
        
        
    def readAudio(self, pressed):
        
        # source = self.sender()
        fileAudioPath = self.openFile()
        # fileAudioPath = "D:/Music/Nablast/TestLeds2.wav"
        Thread(None,processAudio,args=(self,fileAudioPath)).start()
        
    def setRed(self,value):
    
        self.colRed.setRed(value)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colBlue.setRed(value)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
        
        self.colGreen.setRed(value)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
    def setBlue(self,value):
    
        self.colRed.setBlue(value)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colBlue.setBlue(value)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
        
        self.colGreen.setBlue(value)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
    def setGreen(self,value):
    
        self.colRed.setGreen(value)
        self.squareRed.setStyleSheet("QWidget { background-color: %s }" % self.colRed.name())
        
        self.colBlue.setGreen(value)
        self.squareBlue.setStyleSheet("QWidget { background-color: %s }" % self.colBlue.name())
        
        self.colGreen.setGreen(value)
        self.squareGreen.setStyleSheet("QWidget { background-color: %s }" % self.colGreen.name())
        
    def setAmplitudeL(self,value):
        self.vuMeterL.setGeometry(self.wvuMeterL, self.hVuMeter + ratioSizeSquare*3*sizeWindows*(1-value), (ratioSizeSquare/4)*sizeWindows, ratioSizeSquare*3*sizeWindows - ratioSizeSquare*3*sizeWindows*(1-value))
        
    def setAmplitudeR(self,value):
        self.vuMeterR.setGeometry(self.wvuMeterR, self.hVuMeter + ratioSizeSquare*3*sizeWindows*(1-value), (ratioSizeSquare/4)*sizeWindows, ratioSizeSquare*3*sizeWindows - ratioSizeSquare*3*sizeWindows*(1-value))
        
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', '', 'AudioFile (*.wav)')
        return fileName
        
    def changeSquareValue(self,ledId,value):
        thread = changeSquareThread(ledId,value)
        if ledId == 0:
            self.connect(thread, QtCore.SIGNAL("setRed(int)"), self.setRed)
        elif ledId == 1:
            self.connect(thread, QtCore.SIGNAL("setGreen(int)"), self.setGreen)
        elif ledId == 2:
            self.connect(thread, QtCore.SIGNAL("setBlue(int)"), self.setBlue)
        
        thread.start()
        
    def changeAmplitudeValue(self,lr,value):
        thread = changeAmplitudeThread(lr,value)
        if lr == 0:
            self.connect(thread, QtCore.SIGNAL("setAmplitudeL(float)"), self.setAmplitudeL)
        elif lr == 1:
            self.connect(thread, QtCore.SIGNAL("setAmplitudeR(float)"), self.setAmplitudeR)
        thread.start()
        

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
    
    ledsNumber = 32
    
    audio = read_audio(audio_stream_input,audio_stream_output, num_samples=CHUNK,sound=sound, wf=wf)
    
    leds = notes_scaled_nosaturation.process(audio,\
                                                num_leds=ledsNumber,\
                                                num_samples=CHUNK,\
                                                sample_rate=rate,\
                                                falloff_val=smoothness/100.0)
    
    hl = lum_hue(leds, num_leds=ledsNumber)
    colors = colorize(hl)
    
    max = [0,0,0]
    min = [30000,30000,30000]
    
    idLed1 = 10
    idLed2 = 20
    idLed3 = 30
    
    maximal = 0
    
    i = 0

    # for sample, c in zip(audio,colors):
    for c in colors:
        #for sampleL, sampleR in samples:
        
        """

        sampleL = sample[0]
        sampleR = sample[1]
        
        currentAmpL = np.linalg.norm(sampleL)
        currentAmpR = np.linalg.norm(sampleR)
    
        if currentAmpL > maximal:
            maximal = currentAmpL
            
        if currentAmpR > maximal:
            maximal = currentAmpR
        
        currentAmpL = currentAmpL/maximal
        currentAmpR = currentAmpR/maximal
    
        guiObj.changeAmplitudeValue(0,currentAmpL)
        guiObj.changeAmplitudeValue(1,currentAmpR)
        """
            
        c = list(map(lambda x: int(x * 255), c))
        
        r = c[0]
        g = c[1]
        b = c[2]
            
            
        """
        if (led[idLed1] > max[0]):
            max[0] = led[idLed1]
            
        if (led[idLed2] > max[1]):
            max[1] = led[idLed2]

        if (led[idLed3] > max[2]):
            max[2] = led[idLed3]
            
            
        if (led[idLed1] < min[0]):
            min[0] = led[idLed1]
            
        if (led[idLed2] < min[1]):
            min[1] = led[idLed2]
            
        if (led[idLed3] < min[1]):
            min[2] = led[idLed3]
            
        if max[0] != min[0]:
            r = int(255*(led[idLed1]-min[0])/(max[0]-min[0]))
        else:
            r = 255
            
        if max[1] != min[1]:
            g = int(255*(led[idLed2]-min[1])/(max[1]-min[1]))
        else:
            g = 255
            
        if max[2] != min[2]:
            b = int(255*(led[idLed3]-min[2])/(max[2]-min[2]))
        else:
            b = 255
        """
        # print('rgb : ' + str([r,g,b]))
        # print('min : ' + str(min))
        # print('max : ' + str(max))
            
        guiObj.changeSquareValue(0,r)
        guiObj.changeSquareValue(1,g)
        guiObj.changeSquareValue(2,b)
    
    
def processUnit(guiObj,data,maxAudio):
    print('ok')
    
    currentMean = (np.mean(data))
    
    if currentMean > maxAudio:
        maxAudio = currentMean
    
    valueNormalized = 1-currentMean/maxAudio
    guiObj.setRed(255*valueNormalized)
    
    return maxAudio
        
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    ex = MyFirstGUI()
    sys.exit(app.exec_())
    