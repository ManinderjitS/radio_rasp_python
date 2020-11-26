

import bluetooth

from enum import Enum

class HeaderMssgType(Enum):
     SENDTOOUTSIDEWORLD = 1
     SENDTOANDROID = 4
    
     
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
		print("Bluetooth binding exception")
		print(str(e))


#In our case the client almost always will be an Android device 
def blth_listening_client_connection_data():
	print(">>>>>listen client on bluth")
	global blueth_sock, client, clientInfo, got_a_mssg_to_send, out_going_mssg_que
	
	try:
		client, clientInfo = blueth_sock.accept() 
		while 1:
			print("main thread - - - - - - Bluetooth connected: listening for data.") 
			try:
				data = client.recv(size)
				if data:
					data_str = data.decode("utf-8")
					print("\nBlth data received: " + data_str)
					out_going_mssg_que.append(data_str)
					got_a_mssg_to_send = True
			except Exception as e:
				print("bluetooth inner exception : ")
				print(str(e))
		t1.join()
	except Exception as e:	
		print("[Closing socket] ")
		print(e)
		client.close()
		blueth_sock.close()



#This method sends data received from xbee to android using Pi's 
#bluetooth connection with the android		
def send_radio_mssgs_to_android():
	global in_coming_mssg_que, client, radio_mssg_received, android_wants_data
	
	if radio_mssg_received and client:
		print("*****sending mssg from pi to phone")
		for index, mssg in enumerate(in_coming_mssg_que):
			print("---sending back to client: ", mssg)
			client.send(mssg)
			# remove from the original
			del in_coming_mssg_que[index]
	
	if not in_coming_mssg_que:
		radio_mssg_received = False 		


##This is the main function
def main():
	print("Begining the execution of the file here")
	##Instantiate the xbee device
	##Make a bluetooth socket
	bluetooth_socket_binding()
	##Start listening for connection
	blth_listening_client_connection_data()
