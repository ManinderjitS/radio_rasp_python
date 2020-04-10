###This file curently only takes care of sending side, meaning this code 
###	only reads data which a user wants to send, the receiver side still
###	needs to be added.
#B8:27:EB:0A:26:6F

import os
import time
import bluetooth
import threading
import time
from digi.xbee.devices import XBeeDevice

lock = threading.Lock()

device = object()
hostMACAddress = "B8:27:EB:0A:26:6F" #for bluetooth interface
blueth_sock = object()
client = object()
clientInfo = object()
received_android_mssg_que = [] 
received_xbee_mssg_que = []
out_going_mssg_que = []
radio_mssg_received = False
got_a_mssg_to_send = False 

#This class isn't being used yet
class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)
 
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
	global blueth_sock, client, clientInfo, got_a_mssg_to_send
	size = 1024
	
	#start another thread for function which listens for incoming radio mssgs
	t1 = threading.Thread(target=listen_for_radio_mssgs)
	t1.start()
	try:
		client, clientInfo = blueth_sock.accept() 
		#start a second thread to send mssgs received from radio to the 
		#android using bluetooth
		t2 = threading.Thread(target=listen_for_radio_mssgs)
		t2.start()
		while 1:
			print("Bluetooth connected: listening for data.") 
			try:
				data = client.recv(size)
				if data:
					print("Blth mssg received")
					print(data)
					got_a_mssg_to_send = True
					out_going_mssg_que.append(data)
					#~ send_message(data)					
					#client.send(data) # Echo back to client
			except Exception as e:
				print(str(e))
		t1.join()
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
def send_message():	
	global device, out_going_mssg_que	
	if(device):
		for mssg in out_going_mssg_que:
			print("Sending radio mssg: ", mssg)
			device.send_data_broadcast(mssg)
		
#This method sends data received from xbee to android using Pi's 
#bluetooth connection with the android		
def send_radio_mssgs_to_android():
	global received_xbee_mssg_que, client, radio_mssg_received
	while 1:
		if radio_mssg_received:
			with lock:
				for mssg in received_xbee_mssg_que:
					client.send(mssg)
				received_xbee_mssg_que.clear()
				radio_mssg_received = False
		time.sleep(3)
		 		
	
#Listen for mssgs on the radio device		
def listen_for_radio_mssgs():
	global received_xbee_mssg_que, client, clientInfo, radio_mssg_received, got_a_mssg_to_send
	#listen for mssg on radio for 60 sec  
	while 1:
		print("Listening for radio mssgs")
		if got_a_mssg_to_send:
			print("There is a mssg to send")
			send_message()
		else:
			print("No mssg has been received")
		try:
			mssg = device.read_data(10)					
			str_mssg = mssg.data.decode("utf-8")
			#~ with lock:
				#~ print("The lock thing")
			#client.send(mssg)
			received_xbee_mssg_que.append(mssg)
			radio_mssg_received = True
			print("received mssg: " + str_mssg)
		except Exception as e:
			print(str(e))
			continue 

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
	 
