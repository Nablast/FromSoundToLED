import bluetooth
from bluetooth import *
import pdb

bd_addr = "00:19:86:00:00:CE" 
port = 1

pdb.set_trace()

sock = bluetooth.BluetoothSocket (bluetooth.RFCOMM)
sock.connect((bd_addr,port))
while 1:
        tosend = raw_input()
        if tosend != 'q':
			sock.send(tosend)
        else:
			break
sock.close()
