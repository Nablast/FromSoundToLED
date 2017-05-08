import numpy as np
import pyaudio

from LedsValuesComputation import LedsValuesComputation

rate = 44100
CHUNK = 1024

nbLeds = 3
numSpectrumBands = 64

buttonsBool = np.array([[1],[i for i in range(15,24)],[i for i in range(27,63)]])

buttonsBool = np.array([(i in buttonsBool[iLed]) for iLed in range(nbLeds) for i in range(numSpectrumBands)])
buttonsBool = buttonsBool.reshape((nbLeds, numSpectrumBands))

p=pyaudio.PyAudio()

def read_micro(audio_stream_input, num_samples):
        while 1:
            
            # Read all the input data. 
            samples = audio_stream_input.read(num_samples) 
            # Convert input data to numbers
            samplesNp = np.fromstring(samples, dtype=np.int16).astype(np.float)
            samples_l = samplesNp[::2]  
            samples_r = samplesNp[1::2]
            # audio_stream_output.write(samples)
            
            yield (samples_l, samples_r), buttonsBool

LedsComputator = LedsValuesComputation(nbLeds, numSpectrumBands, rate, CHUNK)

audio_stream_input = p.open(format=pyaudio.paInt16,\
                                channels=2,\
                                rate=rate,\
                                input=True,\
                                frames_per_buffer=CHUNK)\

audio = read_micro(audio_stream_input, CHUNK)

valuesGen = LedsComputator.process(audio)

for spectrum, ledsValues, max, min in valuesGen:
    print(ledsValues)