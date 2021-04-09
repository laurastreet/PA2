## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more if you need)
import threading
import sys
import logging
import unreliable_channel
import zlib
import time
from socket import *

DATA = 0
ACK = 1

## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.

# client_port


## we will need a lock to protect against concurrent threads
#NOTE - you cannot receive and send at the same time
lock = threading.Lock()

# take the input file and split it into packets (use create_packet)
# MTU = 1500bytes
# max size of MTU header + data = 1472 bytes
    #MTU header =
    #UDP header = 8 bytes
    #IP header = 20 bytes
def create_packet(data, seqNum):
    #after adding the first 3 fields of MTP data and header, sender calculates a 32-bit checksum and appends it to the packet
    packet = ''
    packet_type = DATA
    length = len(data)
    # print('length: ', length)

    #print('data: ', data, ', seqNum: ', seqNum)
    bytes_arr = bytes(str(packet_type) + str(seqNum) + str(length) + str(data), 'utf-8')
    # print('sizeof(bytes_arr): ', sys.getsizeof(bytes_arr))
    checksum = zlib.crc32(bytes_arr)
    checksum = str(checksum)
    checksum = bytes(checksum, 'utf-8')
    # print('sizeof(checksum): ', sys.getsizeof(checksum))
    # print(type(checksum))
    packet = bytes_arr + checksum
    # print('checksum:', checksum)

    return packet

def extract_packet_info(packet_from_server):
    decoded_packet = packet_from_server.decode('utf-8')
    packet_type = decoded_packet[0:1]
    # seq_num = decoded_packet[1:-2]    ###unsure how to find this, since we don't have length...
    # len = decoded_packet[]
    # checksum = decoded_packet[]
    bytes_arr = []
    corrupt = check_for_corruption(bytes_arr,checksum)
# extract the packet data after receiving
    return seq_num,corrupt

def check_for_corruption(bytes_arr,checksum_sender):
    checksum = zlib.crc32(bytes_arr)
    if(checksum==checksum_sender):
        return False
    else:
        return True

def receive_thread(socket):
    while(True):
        # receive packet, but using our unreliable channel
		packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
        extract_packet_info(packet_from_server)
        # packet = extract_packet_info(packet_from_server)
		# check for corruption, take steps accordingly
		# update window size, timer, triple dup acks


def MTPSender_main(arg):
    print('MTPSender starting')
    lowest_unACKed_seq_num = 0
	# read the command line arguments
    # recv_ip = sys.argv[1]             #127.0.0.1
    # recv_port = sys.argv[2]
    recv_port = 631
    # wind_size = sys.argv[3]       #size of sliding window
    wind_size = 5
    # filename = sys.argv[4]        #filename = './1MB.txt'
    filname = '/home/laura/Downloads/1MB.txt'
    # log_filename = sys.argv[5]

	# open log file and start logging
    # logfile = open(log_filename, "a")

    # open client socket and bind  - 'client opens up a UDP client socket'
    serverAddr = '192.168.1.14'
    receiverAddr = '192.168.1.15'
    serverPort = 49152
    receiverPort = 49153
    sendingSocket = socket(AF_INET, SOCK_DGRAM)  # AF_INET indicates that the underlying network is using IPv4
        # SOCK_DGRAM indicates that socket is a UDP socket
        # the OS creates the port number of the client socket (per textbook)
    sendingSocket.settimeout(5)        #500ms timeout
    receiverSocket = socket(AF_INET, SOCK_DGRAM)
    receiverSocket.bind((receiverAddr,receiverPort))



	# start receive thread
	# recv_thread = threading.Thread(target=receive_thread,args=(clientSocket))
	# recv_thread.start()


	# take the input file and split it into packets (use create_packet)
        #packet data size has to be <= 1472bytes (1472 chars) minus size of header
        #header = 8 bytes unsigned int (type) + 8 bytes unsigned int (seqnum) + 8 bytes unsigned int (length) + checksum (4 bytes)
        #packet data size <= 1472 bytes - 28 bytes = 1444 bytes
    seqNum = 0
    # filename = sys.argv[4]
    input_file = open('/home/laura/Downloads/1MB.txt') #open arg4

        #preprocess input_file
    str = ''
    for line in input_file:
        str += line
    bytes_arr = bytes(str, 'utf-8')
    print(sys.getsizeof(bytes_arr))
    data_size = 1400
    packets = []
    lowest_unACKed_packet = 0
    highest_unACKed_packet = 4
    while(len(bytes_arr)>0):
        data = bytes_arr[0:data_size]
        bytes_arr = bytes_arr[data_size:]
        print(sys.getsizeof(bytes_arr))
        packet = create_packet(data,seqNum)

        packets.append(packet)
        # clientSocket.sendto(packet,serverName)
        sendingSocket.sendto(packet,(serverAddr,serverPort))  # trial to ensure sockets can communicate
        # print('sent packet: ', seqNum)
        time.sleep(0.2)
        seqNum += 1


	# while there are packets to send:
		# send packets to server using our unreliable_channel.send_packet()

        # unreliable_channel.send_packet(clientSocket,packet,recv_port)    #last argument is an open port - 631
		# update the window size, timer, etc.


# MTPSender_main(0)

