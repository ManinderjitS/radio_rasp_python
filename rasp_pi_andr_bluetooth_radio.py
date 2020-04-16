###This file curently only takes care of sending side, meaning this code 
###	only reads data which a user wants to send, the receiver side still
###	needs to be added.
#B8:27:EB:0A:26:6F

import os
import time
import bluetooth
import threading
import time
import json
from digi.xbee.devices import XBeeDevice
from enum import Enum

class HeaderMssgType(Enum):
     SENDTOOUTSIDEWORLD = 1
     SENDTOANDROID = 4

lock = threading.Lock()

device = object()
hostMACAddress = "B8:27:EB:0A:26:6F" #for bluetooth interface
blueth_sock = object()
client = object()
clientInfo = object()
received_android_mssg_que = [] 
received_xbee_mssg_que = {}
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
	print("bbbbbbbbbbbBinding socket")
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
def blth_listening_client_connection_data():
	print(">>>>>listen client on bluth")
	global blueth_sock, client, clientInfo, got_a_mssg_to_send
	size = 1024
	
	#start another thread for function which listens for incoming radio mssgs
	t1 = threading.Thread(target=listen_for_radio_mssgs)
	t1.start()
	try:
		client, clientInfo = blueth_sock.accept() 
		send_radio_mssgs_to_android()
		#start a second thread to send mssgs received from radio to the 
		#android using bluetooth
		t2 = threading.Thread(target=listen_for_radio_mssgs)
		t2.start()
		while 1:
			print("main thread - - - - - - Bluetooth connected: listening for data.") 
			try:
				data = client.recv(size)
				if data:
					print("Blth mssg received")
					top_most_header = data[:data.find('-'.encode("utf-8"))]
					if(int(top_most_header.decode("utf-8")) == HeaderMssgType.SENDTOANDROID.value):
						print("a-a--a-a--aAndroid wants to know if it got somethign")
						send_radio_mssgs_to_android()
					else:
						print("received data to send=-=-=-=-")
						data = data[data.find('\n'.encode("utf-8"))+1:]
						got_a_mssg_to_send = True
						data_json = convert_data_to_json(data.decode("urf-8"))
						out_going_mssg_que.append(data_json)
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
	print("-----------send msssg")
	global device, out_going_mssg_que	
	for index1, mssg in enumerate(out_going_mssg_que):
		print("Sending radio mssg: ", mssg)
		for key, value in mssg.items():
			if(device):
				mssg_to_send = mssg["time"].encode("utf-8") + 
								"-".encode("utf-8") + 
								key.encode("utf-8") + 
								":".encode("utf-8") +
								value.encode("utf-8")
				device.send_data_broadcast(mssg_to_send)
	out_going_mssg_que.clear()
	got_a_mssg_to_send = False
		
#This method sends data received from xbee to android using Pi's 
#bluetooth connection with the android		
def send_radio_mssgs_to_android():
	print("*****sending mssg from pi to phone")
	global received_xbee_mssg_que, client, radio_mssg_received
	if radio_mssg_received:
		for key, value in received_xbee_mssg_que:
			mssg = "{" ##This will be a string json object
			for element in value:
				mssg = mssg + element + ","
			mssg = mssg = "}" 
			print("---sending back to client: " + mssg)
			client.send(mssg)
		received_xbee_mssg_que.clear()
	radio_mssg_received = False
		 		
	
#Listen for mssgs on the radio device		
def listen_for_radio_mssgs():
	print("Listen for radio mssg")
	global received_xbee_mssg_que, client, clientInfo, radio_mssg_received, got_a_mssg_to_send
	#listen for mssg on radio for 60 sec  
	i = 0
	while 1:
		print("Listening for radio mssgs")
		if got_a_mssg_to_send:
			print("There is a mssg to send from the client")
			send_message()
		try:
			mssg = device.read_data(10)					
			received_mssg = mssg.data.decode("utf-8")
			#~ with lock:
				#~ print("The lock thing")
			#client.send(mssg)
			mssg_header = received_mssg[:received_mssg.find('-')]
			received_mssg = received_mssg[received_mssg.find('-')+1:]
			if(mssg_header in received_xbee_mssg_que):
				received_xbee_mssg_que[mssg_header].append(received_mssg)
				radio_mssg_received = True
			else:
				received_android_mssg_que[mssg_header] = []
				received_android_mssg_que[mssg_header].append(received_mssg)
			# ~ send_radio_mssgs_to_android()
			print("received mssg: " + received_mssg)
		except Exception as e:
			print(str(e))
			# ~ send_mssg_driver(i)
			i = i + 1
			continue 

#This function is creating for testing purposes, 
#	its purpose is to send dummy data 
def send_mssg_driver(num_of_times):
	global got_a_mssg_to_send
	print("Inside send_mssg driver")
	sample_str = "{" +
					"time:" + str(num_of_times) + "," +
					"mssgId:" + "Iasdas9129nsa21," +
					"mssgText:" + "hello there, " + str(num_of_times) + "," +
					"receiverId:" + "someID," + 
					"receiverName:" + "someName," + 
					"senderId:" + "someID1," + 
					"senderName:" + "someName1," + 
					"latitude:" + "someLat," +
					"longitude:" + "123.123213," + 
					"mssgType:" + "-123.123123," + 
					"isMyMssg:" + "True," + 
				"}"
					
	out_going_mssg_que.append(sample_str.encode("utf-8"))
	got_a_mssg_to_send = True
	
##This function converts the string received to json
def convert_data_to_json(data):
	data_json = json.loads(data)
	return(data_json)

##This is the main function
def main():
	global device
	print("Begining the execution of the file here")
	##Instantiate the xbee device
	xbee_instance()
	##Make a bluetooth socket
	bluetooth_socket_binding()
	##Start listening for connection
	blth_listening_client_connection_data()
		 
	##Closing the connection
	device.close()

##Letting the Python interpreter about the main function
if __name__ == "__main__":
	main()
	 
