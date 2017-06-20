import wave
import pyaudio

CHUNK = 1024

micro = True

fileAudioPath = 'data/Rituel_With_intro_v10_with_audio_Live_vLed.wav'

p=pyaudio.PyAudio()


	
if micro:						
	rate = 44100
	audio_stream_input = p.open(format=pyaudio.paInt16,\
								channels=2,\
								rate=rate,\
								input=True,\
								frames_per_buffer=CHUNK,\
								input_device_index=0)\

	audio_stream_output =p.open(format=pyaudio.paInt16,\
								channels=2,\
								rate = rate,\
								output=True,\
								frames_per_buffer=CHUNK,\
								input_device_index=0)\

else:
	wf = wave.open(fileAudioPath, 'rb')
	rate = wf.getframerate()

	audio_stream_output =p.open(format=p.get_format_from_width(wf.getsampwidth()),\
									channels=wf.getnchannels(),\
									rate = rate,\
									output=True,\
									frames_per_buffer=CHUNK,\
									output_device_index=0)\


while 1:
	if micro :
		sound = audio_stream_input.read(CHUNK)
	else: 
		sound = wf.readframes(CHUNK)
	audio_stream_output.write(sound)
