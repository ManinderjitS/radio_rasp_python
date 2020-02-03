###This file curently only takes care of sending side, meaning this code 
###	only reads data which a user wants to send, the receiver side still
###	needs to be added.
#B8:27:EB:0A:26:6F

import os
import time
import bluetooth
import threading
from digi.xbee.devices import XBeeDevice

lock = threading.Lock()

device = object()
hostMACAddress = "B8:27:EB:0A:26:6F" #for bluetooth interface
blueth_sock = object()
client = object()
clientInfo = object()
received_android_mssg_que = [] 
received_xbee_mssg_que = []
 
##Creating an instance of XBeeDevice and opening a connection with the device
def xbee_instance():
	global device
	try:
		device = XBeeDevice("/dev/ttyUSB2", 9600)
		device.open()
	except Exception as e:
		print(str(e))
	

##This function makes a bluetooth socket 
def bluetooth_socket_binding():
	global blueth_sock
	port = 0
	backlog = 1
	blueth_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
	try:
		blueth_sock.bind((hostMACAddress, port))
		blueth_sock.listen(backlog)
	except Exception as e:
		print(str(e))

#In our case the client almost always will be an Android device 
def listening_client_connection_data():
	global blueth_sock, client, clientInfo
	size = 1024
	try:
		client, clientInfo = blueth_sock.accept()
		print("Client connected: listening for data.")
		#start another thread for function which listens for incoming radio mssgs
		t = threading.thread.start_new_thread(listen_for_radio_mssgs,())
		while 1:
			try:
				t.start()
				data = client.recv(size)
				if data:
					print(data)
					send_message(data)
					print("Sending back to the client")
					#client.send(data) # Echo back to client
			except Exception as e:
				print(str(e))
	except Exception as e:	
		print("[Closing socket]: " + e)
		client.close()
		blueth_sock.close()

##File where the android device will be writing to 
#~ exists = os.path.isfile('/dev/rfcomm0') 
##This infinite loop is checking from new data received from the user 
##	(android device) every 5 seconds
#~ while(1):
	#~ time.sleep(5)
	#~ if exists:
		#~ file = open("/dev/rfcomm0", "r")
		#~ data_read = file.read()
		#~ if not r:
			#~ print("File is empty, no data to retrieve.")
		#~ else:
			#~ send_message(mssg)
			#~ print(data_read)
	#~ else:
		#~ print("The file doesn't exist. \n\tCheck bluetooth connection with phone.")

##The function that will send the mssg to the radio
def send_message(mssg):
	global device	
	if(device):
		device.send_data_broadcast(mssg)
	
#Listen for mssgs on the radio device		
def listen_for_radio_mssgs():
	global received_xbee_mssg_que, client, clientInfo
	#listen for mssg on radio for 60 sec  
	while 1:
		mssg = device.read_data(60)
		str_mssg = mssg.data.decode("utf-8")
		with lock:
			client.send(mssg)
			print("received mssg: " + str_mssg)

##This is the main function
def main():
	global device
	print("Begining the execution of the file here")
	##Instantiate the xbee device
	xbee_instance()
	##Make a bluetooth socket
	bluetooth_socket_binding()
	##Start listening for connection
	listening_client_connection_data()
		 
	##Closing the connection
	device.close()

##Letting the Python interpreter about the main function
if __name__ == "__main__":
	main()
	 
