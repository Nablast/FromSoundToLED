import numpy as np
import pyaudio
import bluetooth
import time
import os
import traceback

import logging

from LedsValuesComputation import LedsValuesComputation

# Logging
formatLog='%(asctime)s %(message)s'
datefmt='%m/%d/%Y %I:%M:%S %p'
level=logging.DEBUG
i=0
ok = True

if not os.path.exists('log'):
	os.mkdir('log')

while ok:
	logFilePath = 'log/log_' + str(i) + '.log'
	ok = os.path.exists(logFilePath)
	i += 1

logging.basicConfig(filename=logFilePath,format=formatLog, datefmt=datefmt, level=level)

# Bluetooth
bd_addr = "98:D3:36:00:BF:2B" 
port = 1

logging.info("")
logging.info("---------------------------------")
logging.info("Starting script")

rate = 44100
CHUNK = 2048
nbLeds = 3
numSpectrumBands = 64

buttonsBool = np.array([[2],[i for i in range(15,24)],[i for i in range(27,63)]])

buttonsBool = np.array([(i in buttonsBool[iLed]) for iLed in range(nbLeds) for i in range(numSpectrumBands)])
buttonsBool = buttonsBool.reshape((nbLeds, numSpectrumBands))
logging.info("Parameters :")
logging.info("  - Rate : " + str(rate))
logging.info("  - Chunk : " + str(CHUNK))
logging.info("  - NbLeds : " + str(nbLeds))
logging.info("  - numSpectrumBands : " + str(numSpectrumBands))

def read_micro(audio_stream_input, num_samples, audio_stream_output = None):
	while 1:
            
		# Read all the input data. 
		samples = audio_stream_input.read(num_samples) 
		# Convert input data to numbers
		samplesNp = np.fromstring(samples, dtype=np.int16).astype(np.float)
		samples_l = samplesNp[::2]  
		samples_r = samplesNp[1::2]
		
		if audio_stream_output != None:
			audio_stream_output.write(samples)
		
		yield (samples_l, samples_l), buttonsBool

try:
	logging.info("Connect to Bluetooth : " + bd_addr + " on port " + str(port))
	sock = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
	sock.connect((bd_addr,port))
	
	logging.info("Create pyAudio Object")
	p=pyaudio.PyAudio()
	
	infosAudio = '\n' + '\n'.join([y['name'] for y in [p.get_device_info_by_index(x) for x in range(p.get_device_count())]])
	logging.info("Informations about Audio :")
	logging.info(infosAudio)
	
	logging.info("Create LedsComputator Object")
	LedsComputator = LedsValuesComputation(nbLeds, numSpectrumBands, rate, CHUNK)

	logging.info("Create Audio Input with PyAudio")
	audio_stream_input = p.open(format=pyaudio.paInt16,\
									channels=2,\
									rate=rate,\
									input=True,\
									frames_per_buffer=CHUNK,
									input_device_index=0)\
	  
	logging.info("Create Audio Output with PyAudio")                              
	audio_stream_output = p.open(format=pyaudio.paInt16,\
									channels=2,\
									rate=rate,\
									output=True,\
									frames_per_buffer=CHUNK,
									output_device_index=0)\

	logging.info("Launching Computation")
	
	audio = read_micro(audio_stream_input, CHUNK, audio_stream_output)
	
	valuesGen = LedsComputator.process(audio)

	for spectrum, ledsValues, max, min in valuesGen:
			
		text = 'b'
		for v in ledsValues:
			text += str(int(v*255)) + ','
		text = text[:-1]
		text += 'e'
		sock.send(text)
    
except Exception as e:
	logging.error("Error happened : " + str(e))
	logging.error(traceback.format_exc())
	print(e)
