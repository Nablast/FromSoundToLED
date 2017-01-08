import pyaudio
import wave
import sys
from LED_gui_simulation import MyFirstGUI
from PyQt4 import QtGui

import pdb

CHUNK = 1024
    
filepath = "C:\Windows\Media\Alarm01.wav"

wf = wave.open(filepath, 'rb')

app = QtGui.QApplication(sys.argv)
ex = MyFirstGUI()
sys.exit(app.exec_())

# instantiate PyAudio (1)
p = pyaudio.PyAudio()

# open stream (2)
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

# read data
data = wf.readframes(CHUNK)

# play stream (3)
while len(data) > 0:
    stream.write(data)
    data = wf.readframes(CHUNK)

# stop stream (4)
stream.stop_stream()
stream.close()

# close PyAudio (5)
p.terminate()