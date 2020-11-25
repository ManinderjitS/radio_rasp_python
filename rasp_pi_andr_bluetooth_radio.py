###This file curently only takes care of sending side, meaning this code 
###	only reads data which a user wants to send, the receiver side still
###	needs to be added.
#B8:27:EB:0A:26:6F

import os
import time
import bluetooth
import threading
import time
import urllib.request
from digi.xbee.devices import XBeeDevice
# ~ from firebase import Firebase

config = {
	"apiKey": "AAAAOmudVDY:APA91bFzPVjJUwca9fg8jvC4LUOlzeDjzPUYANcXns-Vcx8QtPZBMFAkE-OGu4Dgq42SUkGIPUwYMIXZ3MIBdYpPM7gBggj3NrJL-0fPNK012X6-KBtCO3NBjzaQ_PlcUevmnveT1Tcv",
	"authDomain": "projectId.firebaseapp.com",
	"databaseURL": "https://databaseName.firebaseio.com",
	"storageBucket": "projectId.appspot.com"
}

firebaseConfig = {
	"apiKey": "AIzaSyAveH6IX7dyPiEZUGoJSacxjEtSWS7JeOk",
	"authDomain": "boreas-bf0bb.firebaseapp.com",
	"databaseURL": "https://boreas-bf0bb.firebaseio.com",
	"projectId": "boreas-bf0bb",
	"storageBucket": "boreas-bf0bb.appspot.com",
	"messagingSenderId": "250913575990",
	"appId": "1:250913575990:web:67c9d30e9bbbdf13127497",
	"measurementId": "G-K85HHXB3EP"
}

# ~ firebase = Firebase(firebaseConfig)

lock = threading.Lock()

device = object()
hostMACAddress = "B8:27:EB:0A:26:6F" #for bluetooth interface
blueth_sock = object()
client = object()
clientInfo = object()
received_android_mssg_que = [] 
received_xbee_mssg_que = []
radio_mssg_received = False

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
	global blueth_sock, client, clientInfo
	size = 1024
	
	#start another thread for function which listens for incoming radio mssgs
	# ~ t1 = threading.Thread(target=listen_for_radio_mssgs)
	# ~ t1.start()
	try:
		client, clientInfo = blueth_sock.accept()
		print("Client connected: listening for data.")  
		#start a second thread to send mssgs received from radio to the 
		#android using bluetooth
		t2 = threading.Thread(target=send_radio_mssgs_to_android)
		t2.start()
		while 1:
			try:
				print("Wating for bluetooth data")
				data = client.recv(size)
				if data:
					print(data)
					send_message(data)
					print("Sending back to the client")
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

##The function that will send the mssg through the radio device
def send_message(mssg):
	global device	
	##If this device has internet connection then send the mssg to firebase
	# ~ if(connected_to_internet):
		# ~ write_to_firebase(mssg)
	if(device):## If there is no internet connection then send the mssg to other devices
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
	global received_xbee_mssg_que, client, clientInfo, radio_mssg_received
	#listen for mssg on radio for 60 sec  
	while 1:
		mssg = device.read_data(60)
		str_mssg = mssg.data.decode("utf-8")
		with lock:
			#client.send(mssg)
			received_xbee_mssg_que.append(mssg)
			radio_mssg_received = True
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
	
		
##This function checks if there is an internet connection
def connected_to_internet(host='http://google.com'):
    try:
        urllib.request.urlopen(host) #Python 3.x
        return True
    except:
        return False


##Letting the Python interpreter about the main function
if __name__ == "__main__":
	main()
	 
