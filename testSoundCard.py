import sys

# sys.settrace

import pyaudio
import numpy as np

import pdb

p = pyaudio.PyAudio() # instantiate the pyaudio

# now get a list of all the audio cards or devices to verify the device index used below
for i in range(p.get_device_count()):
	device = p.get_device_info_by_index(i)
	print((i, device['name'], device['maxInputChannels'])) # won't surprise that there is also a maxOutputChannels

CHANNELS  = 2                    # or could be 2 for stereo or dual mono
FORMAT     = pyaudio.paInt16 # 8 bits more than needed for the card but makes the conversion easier later
RATE         = 44100               # of course you might like 44100 which is more of a popular home rate or 96000
FRAMESIZE = 2048                # don't make this too small it just doesn't gather any samples if you do

# Create an input stream with this instance of pyaudio
recorder = p.open(format = FORMAT, channels = CHANNELS, rate = RATE, input = True, input_device_index = 0, frames_per_buffer = FRAMESIZE)

audio_stream_output = p.open(format=FORMAT,\
                                channels=2,\
                                rate=RATE,\
                                output=True,\
                                frames_per_buffer=FRAMESIZE,
                                output_device_index=0)\

# the main loop which will run forever
# and which constantly finds out how many audio samples there are to read
# and then reads them before converting them to floating point numbers

running = True
while running:
	
	buffer_size = recorder.get_read_available()  # how many samples are available?
	if buffer_size> 0:  # only process if there are some ready to process
		sound_string = recorder.read(FRAMESIZE)  # read in as many samples as were ready to be read
		sound_data = np.fromstring(sound_string, dtype=np.int16).astype(np.float) # then convert to floating point numbers
                                                                                    # this is why we had to use 32 bit numbers above
		# now do something with your floating point data here
		audio_stream_output.write(sound_string)
