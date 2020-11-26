

import bluetooth

from enum import Enum

class MssgType(Enum):
	DONESENDINGDATA = "DONE"
	SENDTOOUTSIDEWORLD = 1
	SENDTOANDROID = 4
    
hostMACAddress = "B8:27:EB:0A:26:6F" #for bluetooth interface
blueth_sock = object()
client = None
clientInfo = object()
out_going_mssg_que = []
last_time_mssg_sent_to_phone = 0
got_a_mssg_to_send = False

     
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
def wait_for_clients():
	print(">>>>>listen client on bluth")
	global blueth_sock, client, clientInfo, got_a_mssg_to_send, out_going_mssg_que
	
	client, clientInfo = blueth_sock.accept()
	
	
	wait_for_data()
	
	client.close()
	blueth_sock.close()

def wait_for_data():
	global blueth_sock, client, clientInfo, got_a_mssg_to_send, out_going_mssg_que
	size = 1024
	
	try: 
		while 1:
			print("Bluetooth connected: listening for data.") 
			try:
				print("\twaiting for data")
				data = client.recv(size)
				if data:
					data_str = data.decode("utf-8")
					if(data_str == MssgType.DONESENDINGDATA):
						print("final mssg for this package recieved, closing socket")
						client.close()
						break
					print("\nBlth data received: " + data_str)
					out_going_mssg_que.append(data_str)
					got_a_mssg_to_send = True
			except Exception as e:
				print("bluetooth inner exception : ")
				print(str(e))
				break
	except Exception as e:	
		print("[Closing socket] ")
		print(e)
		client.close()
		
	wait_for_clients()
	

# ~ #This method sends data received from xbee to android using Pi's 
# ~ #bluetooth connection with the android		
# ~ def send_radio_mssgs_to_android():
	# ~ global in_coming_mssg_que, client, radio_mssg_received, android_wants_data
	
	# ~ if radio_mssg_received and client:
		# ~ print("*****sending mssg from pi to phone")
		# ~ for index, mssg in enumerate(in_coming_mssg_que):
			# ~ print("---sending back to client: ", mssg)
			# ~ client.send(mssg)
			# ~ # remove from the original
			# ~ del in_coming_mssg_que[index]
	
	# ~ if not in_coming_mssg_que:
		# ~ radio_mssg_received = False 		


##This is the main function
def main():
	print("Begining the execution of the file here")
	##Instantiate the xbee device
	##Make a bluetooth socket
	bluetooth_socket_binding()
	##Start listening for connection
	wait_for_clients()


##Letting the Python interpreter about the main function
if __name__ == "__main__":
	main()
