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

CHUNK = 256

sizeWindows = 1000
ratioSizeSquare = 0.15

ratioLines = 0.02
spaceBetweenLines = 0.005

numSpectrumBands = 60

smoothness = 70
        
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
        h = sizeWindows*(1/3) - 0.05*sizeWindows/2
        w = sizeWindows*(3/5) - 0.2*sizeWindows/2
        but.move(w, h)
        but.clicked[bool].connect(self.readAudio)
    
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette)
        
        self.col = QtGui.QColor(0, 0, 0)   
        
        # Vu Meter
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
        
        # Spectrum
        self.spectrumLines = []
        self.wSpectrum = []
        self.hSpectrum = sizeWindows*(2/3) - ratioSizeSquare*5*sizeWindows/2
        for i in range(0,numSpectrumBands):
            self.spectrumLines.append(QtGui.QFrame(self))
            self.wSpectrum.append(sizeWindows*(3/5) + (i - numSpectrumBands/2)*(ratioLines+spaceBetweenLines)*sizeWindows)
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, 0, ratioLines*sizeWindows, 0 )
            self.spectrumLines[i].setStyleSheet("QWidget { background-color: %s }" % self.colWhite.name())
        
        self.setWindowTitle('LED Simulation')
        self.show()
        
        test = []
        for i in range(0,numSpectrumBands):
            test.append(i/numSpectrumBands)
        self.setSpectrum(test)
        
    def readAudio(self, pressed):
        
        # source = self.sender()
        fileAudioPath = self.openFile()
        # fileAudioPath = "D:/Music/Nablast/TestLeds2.wav"
        Thread(None,processAudio,args=(self,fileAudioPath)).start()
        
        
    def setAmplitudeL(self,value):
        self.vuMeterL.setGeometry(self.wvuMeterL, self.hVuMeter + ratioSizeSquare*3*sizeWindows*(1-value), (ratioSizeSquare/4)*sizeWindows, ratioSizeSquare*3*sizeWindows - ratioSizeSquare*3*sizeWindows*(1-value))
        
    def setAmplitudeR(self,value):
        self.vuMeterR.setGeometry(self.wvuMeterR, self.hVuMeter + int(ratioSizeSquare*3*sizeWindows*(1-value)), (ratioSizeSquare/4)*sizeWindows, ratioSizeSquare*3*sizeWindows - int(ratioSizeSquare*3*sizeWindows*(1-value)))
        
    def setSpectrum(self,values):
        for i,v in enumerate(values):
            self.spectrumLines[i].setGeometry(self.wSpectrum[i]-ratioLines*sizeWindows/2, int(self.hSpectrum + ratioSizeSquare*3*sizeWindows*(1-v)), ratioLines*sizeWindows, int(ratioSizeSquare*3*sizeWindows - ratioSizeSquare*3*sizeWindows*(1-v)))
    
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', '', 'AudioFile (*.wav)')
        return fileName
        
    def changeAmplitudeValue(self,lr,value):
        thread = changeAmplitudeThread(lr,value)
        if lr == 0:
            self.connect(thread, QtCore.SIGNAL("setAmplitudeL(float)"), self.setAmplitudeL)
        elif lr == 1:
            self.connect(thread, QtCore.SIGNAL("setAmplitudeR(float)"), self.setAmplitudeR)
        thread.start()
        
    def changeSpectrum(self,values):
        thread = changeSpectrumThread(values)
        self.connect(thread, QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.setSpectrum)
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
  
    
    audio = read_audio(audio_stream_input,audio_stream_output, num_samples=CHUNK,sound=sound, wf=wf)
    
    leds = notes_scaled_nosaturation.process(audio,\
                                                num_leds=numSpectrumBands*2,\
                                                num_samples=CHUNK,\
                                                sample_rate=rate,\
                                                falloff_val=smoothness/100.0)
    
    
    max = []
    for i in range(0,numSpectrumBands):
        max.append(0)
        
        
    min = []
    for i in range(0,numSpectrumBands):
        min.append(300000)
        
    i = 0

    # for sample, led in zip(audio,leds):
    maximal = 0
    for led in leds:
        
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
        
        for i in range(0,numSpectrumBands):
            if (led[i] > maximal):
                maximal = led[i] 
                
        spectrumValues = led[0:numSpectrumBands]
            
        guiObj.changeSpectrum(spectrumValues)
    
    
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
    