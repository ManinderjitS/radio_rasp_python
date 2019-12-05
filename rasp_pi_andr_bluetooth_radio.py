###This file curently only takes care of sending side, meaning this code 
###	only reads data which a user wants to send, the receiver side still
###	needs to be added.

import os
import time
from digi.xbee.devices import XBeeDevice

##Make an instance of XBeeDevice and opening a connection with the device
try:
	device = XBeeDevice("/dev/ttyUSB2", 9600)
	device.open()
except Exception as e:
	print(str(e))

##File where the android device will be writing to 
exists = os.path.isfile('/dev/rfcomm0') 

##This infinite loop is checking from new data received from the user 
##	(android device) every 5 seconds
while(1):
	time.sleep(5)
	if exists:
		file = open("/dev/rfcomm0", "r")
		data_read = file.read()
		if not r:
			print("File is empty, no data to retrieve.")
		else:
			send_message(mssg)
			print(data_read)
	else:
		print("The file doesn't exist. \n\tCheck bluetooth connection with phone.")

##Closing the connection
device.close()

##The function that will send the mssg to the radio
def send_message(mssg):
	device.send_data_broadcast(mssg)
