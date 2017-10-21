#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import math
from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from threading import Thread

from LedGuiAudioProcessor import AudioProcessor
from SpectrumGuiObject import SpectrumGuiObject

import pdb

SampleRate = 44100
CHUNK = 1024
nbLeds = 3

if nbLeds == 4:
    frequencySeparators = [[0,110], \
                           [450, 700], \
                           [700,1200], \
                           [5000,5500]]
    smothness = [380, 340, 300, 280]
elif nbLeds == 3:
    frequencySeparators = [[30,110], \
                           [450, 700], \
                           [800,1200]]
    smothness = [300, 275, 300]

from Hue2Rgb import hue2Rgb
from LedGuiObject import LedGuiObject

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


class SoundToLedGUI(QtGui.QWidget):
    
    def __init__(self):
        super(SoundToLedGUI, self).__init__()
        
        self.nbLeds = nbLeds
        self.frequencies = [SampleRate*i/CHUNK for i in range(1,int(CHUNK/2)+1)]
        self.frequencySeparators = frequencySeparators
        
        self.audioProcessor = AudioProcessor(SampleRate, CHUNK, self.nbLeds, frequencySeparators, smothness)
        
        # Define led by Bins
        self.setLedsBinsVar()
        
        # Define Led Colors
        self.setLedColors()
        
        # Init UI
        self.initUI()
        
    def closeEvent(self, evnt):
        self.audioProcessor.stopAudio()
        super(SoundToLedGUI, self).closeEvent(evnt)
        
    def setLedsBinsVar(self):
     
        self.ledByBins = [-2]*int(CHUNK/2)
        self.binsByLed = []
        for i in range(self.nbLeds):
            self.binsByLed.append([])
        for indexBin in range(int(CHUNK/2)):
            currentFreq = self.frequencies[indexBin]
            for iLed in range(len(self.frequencySeparators)):
                if currentFreq >= self.frequencySeparators[iLed][0] and currentFreq < self.frequencySeparators[iLed][1]:
                    self.ledByBins[indexBin] = iLed
                    self.binsByLed[iLed].append(indexBin)
                                    
    def setLedColors(self):
    
        self.ledColors = []
        for iLed in range(self.nbLeds):
            Hue = iLed*360/self.nbLeds
            r,g,b = hue2Rgb(Hue/360.0)
            self.ledColors.append([r,g,b])
        
    def initUI(self):
    
        self.resize(800,800)
        
        # Background
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Background,QtCore.Qt.black)
        self.setPalette(palette) 
        
        # Define Main Layout
        layout_Main = QtGui.QVBoxLayout()
        self.setLayout(layout_Main)
        
        # First Line : Buttons
        layoutButtons = self.initButtonsUI()
        layout_Main.addLayout(layoutButtons)
        layout_Main.setStretchFactor(layoutButtons, 10)
        
        splitter = QtGui.QSplitter(Qt.Vertical, self)
        
        # Second Line : Spectrums
        widgetSpectrums = self.initSpectrumsUI()
        splitter.addWidget(widgetSpectrums)
        
        # Third Line : Leds
        widgetLeds = self.initLedsUI()
        splitter.addWidget(widgetLeds)
        
        # Fourth Line : Parameters
        widgetParameters = self.initParameters()
        splitter.addWidget(widgetParameters)
        
        splitter.setStretchFactor(0,1)
        splitter.setStretchFactor(1,1)
        splitter.setStretchFactor(2,1)

        layout_Main.addWidget(splitter)
        layout_Main.setStretchFactor(splitter, 90)
        
        self.move(300, 150)
        self.setWindowTitle('LedGui2')
        self.show()
        
        print('Total Size :' + str(self.size()))
        print('Splitter Size :' + str(splitter.size()))
        print('Spectrum Size :' + str(widgetSpectrums.size()))
        print('Led Size :' + str(widgetLeds.size()))
        #print('Parameters Size :' + str(widgetParameters.size()))
        
    def initButtonsUI(self):
        
        layout_Buttons = QtGui.QHBoxLayout()
        
        # FirstLine : Buttons Read Local Sound
        button_LocalSound = QtGui.QPushButton('Read Local Sound', self)
        button_LocalSound.setCheckable(True)
        button_LocalSound.clicked[bool].connect(self.processAudioLocal)
        layout_Buttons.addWidget(button_LocalSound)
        
        # FirstLine : Buttons Read Micro Input
        button_MicroInput = QtGui.QPushButton('Read Micro Input', self)
        button_MicroInput.setCheckable(True)
        button_MicroInput.clicked[bool].connect(self.processAudioMicro)
        layout_Buttons.addWidget(button_MicroInput)
        
        return layout_Buttons
        
    def initSpectrumsUI(self):
    
        widgetMain = QWidget(self)
        layout_SpectrumMain = QtGui.QHBoxLayout(widgetMain)
        
        self.spectrumWidgets = [None]*self.nbLeds
        for iLed in range(self.nbLeds):
        
            binValues = [float(iBin+1)/float(len(self.binsByLed[iLed])) for iBin in range(len(self.binsByLed[iLed]))]
            
            self.spectrumWidgets[iLed] = SpectrumGuiObject(self.ledColors[iLed], binValues)
            
            layout_SpectrumMain.addWidget(self.spectrumWidgets[iLed])
            
        return widgetMain
        
           
    def initLedsUI(self):
    
        widgetMain = QWidget(self)
        layout_LedMain = QtGui.QHBoxLayout(widgetMain)
        self.ledWidget = [None]*self.nbLeds
        for iLed in range(self.nbLeds):
        
            self.ledWidget[iLed] = LedGuiObject(self.ledColors[iLed])
            layout_LedMain.addWidget(self.ledWidget[iLed])
            
        return widgetMain
        
    def initParameters(self):
    
        widgetMain = QWidget(self)
        # layout_Parameter = QtGui.QGroupBox('Parameters', widgetMain)
        
        self.rangeSlider = 1000
        
        layout_Grid = QtGui.QGridLayout(widgetMain)
        # layout_Parameter.setLayout(layout_Grid)
        
        # Freq : minFreq <-> maxFreq
        # Value : 0 <-> 1
        # 
        # f(0) - > minFreq 
        # f(1) -> maxFreq
        #
        # f(x) : x -> A*10^x + B
        #
        # conditions :
        # A + B = minFreq
        # A*10 + B = maxFreq
        #
        # A = minFreq - B
        # B = (10*minFreq - maxFreq)/9
        
        minFreq = self.frequencies[0]
        maxFreq = self.frequencies[-1]
        
        self.B = (10.0*minFreq - maxFreq)/9.0
        self.A = minFreq - self.B
        
        self.spinBoxLow = [None]*self.nbLeds
        self.spinBoxHigh = [None]*self.nbLeds
        self.spinBoxSmooth = [None]*self.nbLeds
        self.sliderLow = [None]*self.nbLeds
        self.sliderHigh = [None]*self.nbLeds
        self.sliderSmooth = [None]*self.nbLeds
        
        for i in range(self.nbLeds):
        
            # QSpinBox Low
            self.spinBoxLow[i] = QtGui.QDoubleSpinBox()
            self.spinBoxLow[i].setMinimum(self.frequencies[0])
            self.spinBoxLow[i].setMaximum(self.frequencies[-1])
            self.spinBoxLow[i].setAlignment(QtCore.Qt.AlignCenter)
            self.spinBoxLow[i].editingFinished.connect(lambda x=i, isLow=True: self.onSpinBoxChanged(x, isLow))
            layout_Grid.addWidget(self.spinBoxLow[i], 0, i, 1, 1)
            
            # Slider Low
            self.sliderLow[i] = QtGui.QSlider(QtCore.Qt.Horizontal)
            self.sliderLow[i].setRange(0,self.rangeSlider)
            self.sliderLow[i].valueChanged.connect(lambda state, x=i, isLow=True: self.onSliderChanged(x, isLow))
            layout_Grid.addWidget(self.sliderLow[i], 1, i, 1, 1)
            
            # QSpinBox High
            self.spinBoxHigh[i] = QtGui.QDoubleSpinBox()
            self.spinBoxHigh[i].setMinimum(self.frequencies[0])
            self.spinBoxHigh[i].setMaximum(self.frequencies[-1])
            self.spinBoxHigh[i].setAlignment(QtCore.Qt.AlignCenter)
            self.spinBoxHigh[i].editingFinished.connect(lambda x=i, isLow=False: self.onSpinBoxChanged(x, isLow))
            layout_Grid.addWidget(self.spinBoxHigh[i], 2, i, 1, 1)
            
            # Slider High
            self.sliderHigh[i] = QtGui.QSlider(QtCore.Qt.Horizontal)
            self.sliderHigh[i].setRange(0,self.rangeSlider)
            self.sliderHigh[i].valueChanged.connect(lambda state, x=i, isLow=False: self.onSliderChanged(x, isLow))
            layout_Grid.addWidget(self.sliderHigh[i], 3, i, 1, 1)

            # QSpinBox Smoothness
            self.spinBoxSmooth[i] = QtGui.QDoubleSpinBox()
            self.spinBoxSmooth[i].setMinimum(0)
            self.spinBoxSmooth[i].setMaximum(1000)
            self.spinBoxSmooth[i].setAlignment(QtCore.Qt.AlignCenter)
            self.spinBoxSmooth[i].editingFinished.connect(lambda x=i,: self.onSpinBoxSmoothChanged(x))
            layout_Grid.addWidget(self.spinBoxSmooth[i], 4, i, 1, 1)
            
            # Slider Smoothness
            self.sliderSmooth[i] = QtGui.QSlider(QtCore.Qt.Horizontal)
            self.sliderSmooth[i].setRange(0,self.rangeSlider)
            self.sliderSmooth[i].valueChanged.connect(lambda state, x=i: self.onSliderSmoothChanged(x))
            layout_Grid.addWidget(self.sliderSmooth[i], 5, i, 1, 1)
            
            # have to be at the end to set also sliders
            self.spinBoxLow[i].setValue(frequencySeparators[i][0])
            self.spinBoxLow[i].editingFinished.emit()
            self.spinBoxHigh[i].setValue(frequencySeparators[i][1])
            self.spinBoxHigh[i].editingFinished.emit()
            self.spinBoxSmooth[i].setValue(smothness[i])
            self.spinBoxSmooth[i].editingFinished.emit()
        
        return widgetMain
        
    def addLineToSpectrum(self, iLed, value, currentColor):
        
        widgetLine = QtGui.QWidget()
        
        layout_SpectrumLine = QtGui.QVBoxLayout()
            
        frame_SpectrumLine = QtGui.QFrame()
        frame_SpectrumLine.setFrameShape(QtGui.QFrame.StyledPanel)
        r,g,b = currentColor
        currentColorStr = "background-color: rgb(%i, %i, %i)" % (r,g,b)
        
        frame_SpectrumLine.setStyleSheet(currentColorStr)
        
        layout_SpectrumLine.addStretch(100-int(value*100.0))
        layout_SpectrumLine.addWidget(frame_SpectrumLine, QtCore.Qt.AlignBottom)
        layout_SpectrumLine.setStretchFactor(frame_SpectrumLine, int(value*100.0))
        layout_SpectrumLine.setSpacing(0)
        
        # widgetLine.setLayout(layout_SpectrumLine)
        
        self.layoutSpectrums[iLed].addLayout(layout_SpectrumLine)
        
    def removeLineFromSpectrum(self, iLed):
    
        widgetLineLayout = self.layoutSpectrums[iLed].takeAt(self.layoutSpectrums[iLed].count()-1)
    
        frame = widgetLineLayout.takeAt(1)
        stretch = widgetLineLayout.takeAt(0)
        
        frame.widget().setParent(None)
    
        widgetLineLayout.setParent(None)
        widgetLineLayout.deleteLater()
        
    def onSpinBoxSmoothChanged(self, iLed):
        
        smoothValue = float(self.spinBoxSmooth[iLed].value())
        
        self.sliderSmooth[iLed].setValue(int(smoothValue*self.rangeSlider / 1000.0 ))
        
        self.audioProcessor.setSmoothness(iLed, smoothValue)  
        
    def onSpinBoxChanged(self, iLed, isLow):
    
        fMin = float(self.spinBoxLow[iLed].value())
        fMax = float(self.spinBoxHigh[iLed].value())
        
        if isLow:
  
            if fMin > fMax:
                self.spinBoxHigh[iLed].setValue(fMin)
                
            xMin = math.log10((fMin - self.B) / self.A)
            self.sliderLow[iLed].setValue(int(xMin*self.rangeSlider))
        else:
            if fMax < fMin:
                self.spinBoxLow[iLed].setValue(fMax)
                
            xMax = math.log10((fMax - self.B) / self.A)
            self.sliderHigh[iLed].setValue(int(xMax*self.rangeSlider))
            
        self.audioProcessor.setFrequencySeparators(iLed, fMin, fMax)    
        
    def onSliderSmoothChanged(self, iLed):

        smoothValue = float(self.sliderSmooth[iLed].value()) * 1000.0 / float(self.rangeSlider)
        
        self.spinBoxSmooth[iLed].setValue(smoothValue) 
        
        self.audioProcessor.setSmoothness(iLed, smoothValue)
    
    def onSliderChanged(self, iLed, isLow):
        
        xMin = float(self.sliderLow[iLed].value()) / float(self.rangeSlider)
        xMax = float(self.sliderHigh[iLed].value()) / float(self.rangeSlider)
        
        if xMax < xMin:
            if isLow:
                xMax = xMin
                self.sliderHigh[iLed].setValue(xMax*float(self.rangeSlider))  
            else:
                xMin = xMax
                self.sliderLow[iLed].setValue(xMin*float(self.rangeSlider))  
            
        fMin = (self.A * float(math.pow(10,xMin))) + self.B
        fMax = (self.A * float(math.pow(10,xMax))) + self.B
        
        self.spinBoxLow[iLed].setValue(fMin)
        self.spinBoxHigh[iLed].setValue(fMax)
        
        self.audioProcessor.setFrequencySeparators(iLed, fMin, fMax)
           
    def changeLeds(self,values):
        thread = changeLedsThread(values)
        self.connect(thread, QtCore.SIGNAL("setLeds(PyQt_PyObject)"), self.setLeds)
        thread.start()
        
    def setLeds(self,valuesForEachLed):
        
        for i in range(self.nbLeds):
            self.ledWidget[i].setLedValue(valuesForEachLed[i])
        
    def changeSpectrums(self,values):
        thread = changeSpectrumThread(values)
        self.connect(thread, QtCore.SIGNAL("setSpectrum(PyQt_PyObject)"), self.setSpectrums)
        thread.start()
        
    def setSpectrums(self,values):
       
        for iLed in range(self.nbLeds):
            self.spectrumWidgets[iLed].setSpectrum(values[iLed])
        
    def changeMinAndMaxOnSpectrum(self,valuesMax,valuesMin, threashL, threashH):
        thread = changeMinAndMaxOnSpectrumThread(valuesMax,valuesMin, threashL, threashH)
        self.connect(thread, QtCore.SIGNAL("setMinAndMaxOnSpectrum(PyQt_PyObject)"), self.setMinAndMaxOnSpectrum)
        thread.start()
        
    def setMinAndMaxOnSpectrum(self,valuesMaxMinThreshLU):
        
        valuesMax = valuesMaxMinThreshLU[0]
        valuesMin = valuesMaxMinThreshLU[1]
        threashLow = valuesMaxMinThreshLU[2]
        threashHigh = valuesMaxMinThreshLU[3]
        
        for iLed in range(self.nbLeds):
            self.spectrumWidgets[iLed].setMinMax(valuesMin[iLed], valuesMax[iLed])
           
    def processAudioLocal(self, pressed):
        
        fileAudioPath = self.openFile()
        Thread(None,self.audioProcessor.process,args=(self,fileAudioPath,True)).start()

    def processAudioMicro(self, pressed):
        
        Thread(None,self.audioProcessor.process,args=(self,'',False)).start()
        
    def openFile(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, 'OpenFile', 'D://DevProjects//FromSoundToLED//data', 'AudioFile (*.wav)')
        return fileName
        
def main():
    app = QtGui.QApplication(sys.argv)
    ex = SoundToLedGUI()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()