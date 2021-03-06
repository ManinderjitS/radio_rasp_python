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
import traceback
import logging

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-9s) %(message)s',)

from digi.xbee.devices import XBeeDevice
from enum import Enum

class MssgType(Enum):
	DONESENDINGDATA = "DONE"
	SENDTOOUTSIDEWORLD = 1
	SENDTOANDROID = 4

lock = threading.Lock()

device = object()
hostMACAddress = "some mac address of the bluetooth interface" 
blueth_sock = object()
client = None
clientInfo = object()
in_coming_mssg_que = []
out_going_mssg_que = []
out_going_str = ""
in_coming_str = ""
last_time_mssg_sent_to_phone = 0
radio_mssg_received = False
got_a_mssg_to_send = False 

#Test related vars
blth_pckts_recvd = 0
rad_pckts_sent = 0
rad_pckts_recvd = 0
blth_pckts_sent = 0

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
		print("Xbee exception")
		print(str(e))
	

##This function makes a bluetooth socket 
def bluetooth_socket_binding():
	print("bbbbbbbbbbbBinding socket")
	global blueth_sock
	port = 0
	backlog = 1
	blueth_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
	try:
		# ~ blueth_sock.bind((hostMACAddress, port))
		blueth_sock.bind((hostMACAddress, port))
		blueth_sock.listen(backlog)
	except Exception as e:
		print("Bluetooth binding exception")
		print(str(e))

#In our case the client almost always will be an Android device 
def blth_listening_client_connection_data():
	print(">>>>>listen client on bluth")
	global blueth_sock, client, clientInfo, got_a_mssg_to_send, out_going_mssg_que, blth_pckts_recvd
	size = 2048
	
	#start another thread for function which listens for incoming radio mssgs
	t1 = threading.Thread(name="radio_thread",target=listen_for_radio_mssgs)
	t1.start()
	while 1:
		try:
			print("wating for clients:")
			client, clientInfo = blueth_sock.accept() 
			#start a second thread to send mssgs received from radio to the android using bluetooth
			#t2 = threading.Thread(name="",target=listen_for_radio_mssgs)
			#t2.start()
			while 1:
				print("main thread - - - - - - Bluetooth connected: listening for data.") 
				try:
					data = client.recv(size)
					if data:
						data_str = data.decode("utf-8")
						if(data_str == "DONE"):
							print("\n\t\t\tdone yo")
							client.close()
							break
						elif(data_str == "ANYTHINGFORME"):
							print("\n\t\t" + out_going_str + " yo")
							send_radio_mssgs_to_android()
							client.close()
							break
						print("\nBlth data received: " + data_str)
						out_going_mssg_que.append(data_str)
						blth_pckts_recvd += 1
						got_a_mssg_to_send = True
				except Exception as e:
					print(str(e))
					print("bluetooth inner exception closing client")
					client.close()
					break
			
		except Exception as e:	
			print("[Closing socket]: " + e)
			client.close()
			blueth_sock.close()
		
		print("\tClosing socket")
		#wait for new client	
		client.close()
	
	t1.join()
	blueth_sock.close()

##This function sends the mssges thru the radio to the outside world
def send_message_through_radio():	
	global device, out_going_mssg_que, rad_pckts_sent, blth_pckts_recvd
		
	print("---------------------Blth pckts recvd: \n\t", blth_pckts_recvd)
	blth_pckts_recvd = 0
	
	for index, mssg in enumerate(out_going_mssg_que):
		mssg_divider = "</e_tag>"
		split_mssg = mssg.split(mssg_divider)
		for index, sub_mssg in enumerate(split_mssg):
			sub_mssg = sub_mssg + mssg_divider
			if(device):
				try:
					print("\tSending radio mssg: ", sub_mssg)
					device.send_data_broadcast(sub_mssg)
					rad_pckts_sent += 1
					#Wait 2 sec before sending another package
					time.sleep(1)
				except Exception as e:
					print("Radio exception: ")
					print(str(e))
					continue
	print("\t\t-------------------Packets sent: ", rad_pckts_sent)
	rad_pckts_sent = 0
	out_going_mssg_que.clear()
	print(str(len(out_going_mssg_que)) + "\n")
	got_a_mssg_to_send = False
		
#This method sends data received from xbee to android using Pi's 
#bluetooth connection with the android		
def send_radio_mssgs_to_android():
	global in_coming_mssg_que, client, radio_mssg_received, android_wants_data, in_coming_str, blth_pckts_sent, rad_pckts_recvd
	
	print("------------------------mssg received form radio: \n\t", rad_pckts_recvd)
	rad_pckts_recvd = 0
	if radio_mssg_received and client:
		print("*****sending mssg from pi to phone\n" + in_coming_str)
		# ~ client.send(in_coming_str)
		for index, mssg in enumerate(in_coming_mssg_que):
			print("---sending back to client: ", mssg)
			blth_pckts_sent += 1
			client.send(mssg)
			# ~ # remove from the original
			# ~ del in_coming_mssg_que[index]
		client.send("DONE")
		time.sleep(10)
	in_coming_mssg_que.clear()
	print("---------------------------------\n\t", blth_pckts_sent)
	blth_pckts_sent = 0
	if not in_coming_mssg_que:
		radio_mssg_received = False 		
	
#Listen for mssgs on the radio device		
def listen_for_radio_mssgs():
	print("Listen for radio mssg")
	global in_coming_mssg_que, client, clientInfo, radio_mssg_received, got_a_mssg_to_send, last_time_mssg_sent_to_phone, in_coming_str, rad_pckts_recvd
	#listen for mssg on radio for 60 sec  
	i = 0
	while 1:
		print("Listening for radio mssgs")
		try:
			mssg = device.read_data(10)					
			received_mssg = mssg.data.decode("utf-8")
			print("recieved from radio: " + received_mssg)
			in_coming_mssg_que.append(received_mssg)
			rad_pckts_recvd += 1 
			in_coming_str = in_coming_str + received_mssg
			radio_mssg_received = True
			
			if got_a_mssg_to_send:
				print("Send the qeued mssg before listening on radio again.")
				send_message_through_radio()
		except Exception as e:
			print("incoming message --- exception")
			print(str(e))
			if got_a_mssg_to_send:
				print("Send the qeued mssg before listening on radio again in exception.")
				send_message_through_radio()
				continue
			# ~ send_mssg_driver(i)
			
		# ~ if(last_time_mssg_sent_to_phone == 0):
			# ~ time_now = int(round(time.time() * 1000))
			# ~ send_radio_mssgs_to_android()
			# ~ last_time_mssg_sent_to_phone = time_now
		# ~ else:
			# ~ time_now = int(round(time.time() * 1000))
			# ~ time_diff = time_now - last_time_mssg_sent_to_phone
			# ~ if(time_diff > 20):
				# ~ last_time_mssg_sent_to_phone = time_now
				# ~ send_radio_mssgs_to_android()
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
					"senderId": "9fb4464d35109faca1005d060878a125",
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
def append_mssg_from_xbee(received_mssg):
	global in_coming_mssg_que, radio_mssg_received
	
	print("\tappende_mssg thread: " + received_mssg)
	radio_mssg_received = True

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
