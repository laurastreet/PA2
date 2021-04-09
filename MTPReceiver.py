## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish

## import (add more if you need)
import unreliable_channel
from socket import *
import sys
import time
import zlib
DATA = 0
ACK = 1

#ACK packets have the same fields as the data packets, without any data
def create_packet(seq_num):
	packet_type = 1

	length = 0		#ACK packets do not contain data
	bytes_arr = bytes(str(packet_type) + str(seq_num) + str(length),'utf-8')
	checksum = zlib.crc32(bytes_arr)
	checksum = str(checksum)
	checksum = bytes(checksum, 'utf-8')
	packet = bytes_arr + checksum
	return packet


#should return the sequence number of packet and whether it is corrupt or not
#note that the checksum length usually seems to equal 10, but sometimes it also equals 9 or 8
def extract_packet_info(ModifiedMessage):
	print('sys.getsizeof(ModifiedMessage): ', sys.getsizeof(ModifiedMessage))		#between 1470-1472 bytes
	print('ModifiedMessage: ', ModifiedMessage)
	decoded_packet = ModifiedMessage.decode('utf-8')
	print('decoded_packet: ', decoded_packet)
	end_numSeq = decoded_packet.find('1400')
	print('end_numSeq')

	packet_type = ModifiedMessage[0:1]
	seq_num = ModifiedMessage[1:end_numSeq]		#this is sandwiched in between packet_type and length (will vary but Receiver will
		#eventually know what to expect) - keep at length 1 for now
	print('seq_num: ', seq_num)
	length = 1400 									#this is fixed

	bytes_arr = bytes(decoded_packet[0:-10], 'utf-8')
	checksum = decoded_packet[-10:]
	if(checksum[0]=='\''):
		checksum = checksum[1:]
		bytes_arr = bytes(decoded_packet[0:-9], 'utf-8')
	checksum = int(checksum)
	print('checksum_sender: ', checksum)
	corrupt = check_for_corruption(bytes_arr, checksum)
	print('corrupt: ', corrupt)
	return seq_num, corrupt
# extract the packet data after receiving

def check_for_corruption(bytes_arr, checksum_sender):
	checksum = zlib.crc32(bytes_arr)				#returns an integer
	print('checksum: ', checksum)
	if(checksum == checksum_sender):
		return False
	else:
		return True

def MTPReceiver_main(arg):
	print('MTPReceiver starting')
	expected_seqNum = 0
	ACK = 'ACK' + str(expected_seqNum)
	# read the command line arguments
	# receiver_port = sys.argv[1]
	# output_file = sys.argv[2]
	# log_filename = sys.argv[3]

	# open log file and start logging
	# logfile = open(log_filename, "a")

	# open server socket and bind
	receiverAddr = '192.168.1.14'
	serverAddr = '192.168.1.15'
	receiverPort = 49152
	serverPort = 49153  # other port can be 631
	receiverSocket = socket(AF_INET, SOCK_DGRAM)  # AF_INET indicates that the underlying network is using IPv4
		# SOCK_DGRAM indicates that socket is a UDP socket
		# the OS creates the port number of the client socket (per textbook)
	receiverSocket.bind((receiverAddr,receiverPort))
	print('socket bound - MTPReceiver')
	receiverSocket.settimeout(5)  # 5s timeout (change to 500ms later)
	sendingSocket = socket(AF_INET, SOCK_DGRAM)


	while(True):
		# receive packet, but using our unreliable channel
		# received_data, recv_addr = unreliable_channel.recv_packet(clientSocket)  # last argument is an open port
		modifiedMessage, serverAddress = receiverSocket.recvfrom(2048)  # modifiedMessage contains packet data - 2048 is the buffer size
		# print('serverAddress: ', serverAddress)
		time.sleep(0.2)
		# call extract_packet_info
		seq_num, corrupt = extract_packet_info(modifiedMessage)
		if(seq_num==expected_seqNum and not corrupt):
			# check for corruption and lost packets, send ack accordingly
			ACK = create_packet(seq_num)
			sendingSocket.sendto(ACK, (serverAddr, serverPort))
			expected_seqNum +=1
			# ACK = 'ACK' + str(expected_seqNum)

MTPReceiver_main(0)

