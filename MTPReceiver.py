## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish

## import (add more if you need)
import unreliable_channel
from socket import *
import sys
import threading
import time
import zlib
DATA = 0
ACK = 1
# channelLock = threading.Semaphore(0)
receiveLock = threading.Semaphore(1)	#start with receive_thread
sendLock = threading.Semaphore(0)

logfile = open("new_logfile.txt", 'w')
ACKsent = 0
packetsAvailable = 0
# sentlock = threading.Lock()
# receiveLock = threading.Lock()
threadlock = threading.Lock()


#ACK packets have the same fields as the data packets, without any data
def create_packet(seq_num):
	packet_type = 1
	length = '0x0'		#ACK packets do not contain data
	bytes_arr = bytes(str(packet_type) + str(seq_num) + length,'utf-8')
	checksum = zlib.crc32(bytes_arr)
	checksum = str(checksum)
	checksum = bytes(checksum, 'utf-8')
	packet = bytes_arr + checksum
	return packet, checksum

def log_packet_info(packet):
    decoded_packet = packet.decode('utf-8')

    # print('decoded_packet: ', decoded_packet)
    packet_type = decoded_packet[0:1]
    str_type = 'DATA' if packet_type == 0 else 'ACK'
    if (str_type == 'DATA'):
        end_seqNum = decoded_packet.find('1400')
        seq_num = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
        len = decoded_packet[end_seqNum:end_seqNum + 4]  # len sent_packet = 1400
        data = decoded_packet[end_seqNum + 4:end_seqNum + 1404]
        checksum = decoded_packet[end_seqNum + 1404:]
        checksum = int(checksum)
    else:
        end_seqNum = decoded_packet.find('0x')
        seq_num = decoded_packet[1:end_seqNum]
        len = decoded_packet[end_seqNum + 2:end_seqNum + 3]  # get rid of '0x'
        checksum = decoded_packet[end_seqNum + 3:]  # no data in ACK packet
	global logfile
	print('Packet sent; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum=', checksum, file=logfile)


#should return the sequence number of packet and whether it is corrupt or not
#note that the checksum length usually seems to equal 10, but sometimes it also equals 9 or 8
def extract_packet_info(ModifiedMessage):
	# print('sys.getsizeof(ModifiedMessage): ', sys.getsizeof(ModifiedMessage))		#between 1470-1472 bytes
	# print('ModifiedMessage: ', ModifiedMessage)
	decoded_packet = ModifiedMessage.decode('utf-8')
	# print('decoded_packet: ', decoded_packet)
	end_seqNum = decoded_packet.find('1400')

	packet_type = decoded_packet[0:1]
	str_type = 'DATA' if packet_type == 0 else 'ACK'
	# print('packet_type: ', packet_type)
	seq_num = decoded_packet[1:end_seqNum]		#this is sandwiched in between packet_type and length (will vary but Receiver will
		#eventually know what to expect) - keep at length 1 for now
	# print(f"ModifiedMessage: {ModifiedMessage}")
	seq_num = int(seq_num)
	length = decoded_packet[end_seqNum:end_seqNum+4]
	# print('length: ', length)						#this is fixed
	data = decoded_packet[end_seqNum+4:end_seqNum+1404]
	# print('data: ', data)
	checksum = decoded_packet[end_seqNum+1404:]
	bytes_arr = bytes(str(packet_type) + str(seq_num) + str(length) + str(data), 'utf-8')
	# checksum = decoded_packet[-10:]
	# if(checksum[0]=='\''):
	# 	checksum = checksum[1:]
	# 	bytes_arr = bytes(decoded_packet[0:-9], 'utf-8')
	# print('type(checksum_sender): ', type(checksum))
	# print('checksum_sender: ', checksum)
	checksum_calc, corrupt = check_for_corruption(bytes_arr, checksum)
	status = 'NOT_CORRUPT' if not corrupt else 'CORRUPT'
	global logfile
	print('Packet received; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum_in_packet=',
		  checksum, '; checksum_calculated=',
		  checksum_calc, 'status=', status, file=logfile)
	return seq_num, corrupt, checksum
# extract the packet data after receiving

def check_for_corruption(bytes_arr, checksum_sender):
	checksum = zlib.crc32(bytes_arr)				#returns an integer
	checksum = str(checksum)
	# print('checksum: ', checksum)
	if(checksum == checksum_sender):
		return checksum, False
	else:
		return checksum, True

def receiver_thread(receiverSocket):
	while True:
		receiveLock.acquire()		#receive lock count starts at 1
		global packetsAvailable		#this will initially be zero (no packets received)
		while(packetsAvailable<5):
			global threadlock
			threadlock.acquire()
			packet, serverAddress = receiverSocket.recvfrom(2048)  # modifiedMessage contains packet data - 2048 is the buffer size
			packetsAvailable+=1
			seq_num, corrupt, checksum = extract_packet_info(packet)
			print('packet: ', seq_num, ' received, corrupt ', corrupt, ', checksum: ', checksum)
			# time.sleep(2)
			threadlock.release()
		sendLock.release()		#increment sendLock so it can send ACKs
			# channelLock.release()			#increments semaphore (sends ACK once it receives packet)



#sends ACK for last correctly received packet
def sender_thread(socket,serverAddr,serverPort):
	while True:
		sendLock.acquire()			#this will initially be blocked until packets have been received by receive_thread
		global packetsAvailable
		while(packetsAvailable>0):
			global threadlock
			threadlock.acquire()
			global ACKsent
			packet,checksum = create_packet(ACKsent)					#ACKsent = seqNum
			socket.sendto(packet, (serverAddr, serverPort))
			# sentlock.release()
			print('ACK: ', ACKsent, 'sent, checksum ', checksum)
			# time.sleep(2)
			ACKsent += 1
			packetsAvailable-=1
			threadlock.release()
		receiveLock.release()		#increment receiveLock so it can receive more packets

def MTPReceiver_main(arg):
	print('MTPReceiver starting')
	expected_seqNum = 0
	# read the command line arguments
	# receiver_port = sys.argv[1]
	# output_file = sys.argv[2]
	# log_filename = sys.argv[3]

	# open log file and start logging
	# logfile = open(log_filename, "a")

	log_filename = 'receiver_log.txt'

	# open log file and start logging
	global logfile
	logfile = open(log_filename, "w")
	#set up sockets
	receiverAddr = '192.168.1.14'
	# receiverAddr = '172.20.10.5'
	serverAddr = '192.168.1.15'
	receiverPort = 49152
	serverPort = 50000  # other port can be 631
	receiverSocket = socket(AF_INET, SOCK_DGRAM)  # AF_INET indicates that the underlying network is using IPv4
		# SOCK_DGRAM indicates that socket is a UDP socket
		# the OS creates the port number of the client socket (per textbook)
	receiverSocket.bind((receiverAddr,receiverPort))
	print('socket bound - MTPReceiver')
	# receiverSocket.settimeout(5)  # 5s timeout (change to 500ms later)
	sendingSocket = socket(AF_INET, SOCK_DGRAM)

	#create threads and start
	senderThread = threading.Thread(target=sender_thread, args=(sendingSocket, serverAddr, serverPort,))
	receiverThread = threading.Thread(target=receiver_thread, args=(receiverSocket,))

	receiverThread.start()
	senderThread.start()

MTPReceiver_main(0)
