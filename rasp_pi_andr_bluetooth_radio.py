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
import copy
from digi.xbee.devices import XBeeDevice
from enum import Enum

class HeaderMssgType(Enum):
     SENDTOOUTSIDEWORLD = 1
     SENDTOANDROID = 4

lock = threading.Lock()

device = object()
hostMACAddress = "B8:27:EB:0A:26:6F" #for bluetooth interface
blueth_sock = object()
client = None
clientInfo = object()
in_coming_mssg_que = {}
out_going_mssg_que = []
last_time_mssg_sent_to_phone = 0
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
					print("received data to send=-=-=-=-")
					data = data[data.find('\n'.encode("utf-8"))+1:]
					got_a_mssg_to_send = True
					data_json = convert_data_to_json(data.decode("utf-8"))
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
def send_message_through_radio():	
	print("-----------send msssg: ")
	global device, out_going_mssg_que	
	for index1, mssg in enumerate(out_going_mssg_que):
		print("Sending radio mssg: ", mssg)
		for key, value in mssg.items():
			if(device):
				mssg_to_send = mssg["time"] + "-" + key + ":" + value
				device.send_data_broadcast(mssg_to_send.encode("utf-8"))
	out_going_mssg_que.clear()
	got_a_mssg_to_send = False
		
#This method sends data received from xbee to android using Pi's 
#bluetooth connection with the android		
def send_radio_mssgs_to_android():
	print("*****sending mssg from pi to phone")
	global in_coming_mssg_que, client, radio_mssg_received, android_wants_data
	
	if radio_mssg_received and client:
		copied_queue = copy.deepcopy(in_coming_mssg_que)
		for key, value in copied_queue.items():
			if(len(value) == 11):
				mssg = "{" ##This will be a string json object
				for index, element in enumerate(value):
					if index < len(value) - 1:
						mssg = mssg + element + ","
					elif index == len(value) - 1:
						mssg = mssg + element
				mssg = mssg + "}" 
				print("---sending back to client: ", mssg)
				client.send(mssg)
				# remove from the original
				del in_coming_mssg_que[key]
	
	if not in_coming_mssg_que:
		radio_mssg_received = False 		
	
#Listen for mssgs on the radio device		
def listen_for_radio_mssgs():
	print("Listen for radio mssg")
	global in_coming_mssg_que, client, clientInfo, radio_mssg_received, got_a_mssg_to_send, last_time_mssg_sent_to_phone
	#listen for mssg on radio for 60 sec  
	i = 0
	while 1:
		print("Listening for radio mssgs")
		if got_a_mssg_to_send:
			print("There is a mssg to send from the client")
			send_message_through_radio()
		try:
			mssg = device.read_data(10)					
			received_mssg = mssg.data.decode("utf-8")
			#~ with lock:
				#~ print("The lock thing")
			#client.send(mssg)
			mssg_header = received_mssg[:received_mssg.find('-')]
			received_mssg = received_mssg[received_mssg.find('-')+1:]
			
			append_mssg_from_xbee(mssg_header, received_mssg)			
		except Exception as e:
			print(str(e))
			# ~ send_mssg_driver(i)
			
		if(last_time_mssg_sent_to_phone == 0):
			time_now = int(round(time.time() * 1000))
			send_radio_mssgs_to_android()
			last_time_mssg_sent_to_phone = time_now
		else:
			time_now = int(round(time.time() * 1000))
			time_diff = time_now - last_time_mssg_sent_to_phone
			if(time_diff > 20):
				last_time_mssg_sent_to_phone = time_now
				send_radio_mssgs_to_android()
		i = i + 1

#This function is creating for testing purposes, 
#	its purpose is to send dummy data 
def send_mssg_driver(num_of_times):
	global got_a_mssg_to_send
	print("Inside send_mssg driver")
	sample_mssg = {
					"time": str(num_of_times),
					"mssgId": "Iasdas9129nsa21",
					"mssgText": "hello there, " + str(num_of_times),
					"receiverId": "someID",
					"receiverName": "someName",
					"senderId": "someID1",
					"senderName": "someName1",
					"latitude": "123.123213",
					"longitude": "-123.123213",
					"mssgType": "1",
					"isMyMssg": "True",
				}
	out_going_mssg_que.append(sample_mssg)				
	got_a_mssg_to_send = True
	
##This function converts the string received to json
def convert_data_to_json(data):
	data_json = json.loads(data)
	print(data,"\n\t", data_json)
	return(data_json)

##This function will be run inside a function
def append_mssg_from_xbee(mssg_header, received_mssg):
	global in_coming_mssg_que, radio_mssg_received
	
	##The message is the time of this received message. Since the message 
	##	is received in parts, we wanna put it together correctly, and since 
	##	the time of the message will be a unique value, it is a good key to 
	##	use for collecting the message together inside the message_recvg_fom_xbee dictionary
	if(mssg_header in in_coming_mssg_que):
		print("\tappende_mssg thread: key exists")
		in_coming_mssg_que[mssg_header].append(received_mssg)
		radio_mssg_received = True
		print(in_coming_mssg_que[mssg_header])
	else:
		print("\tappende_mssg thread: key doesn't exist")
		in_coming_mssg_que[mssg_header] = []
		in_coming_mssg_que[mssg_header].append(received_mssg)
		print(in_coming_mssg_que, "\n\t", received_mssg)

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
	 
