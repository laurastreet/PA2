## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish


## import (add more if you need)
import threading
import sys
import logging
import unreliable_channel
import zlib
from socket import *

DATA = 0
ACK = 1

## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.

# client_port


## we will need a lock to protect against concurrent threads
# lock = threading.Lock()

# take the input file and split it into packets (use create_packet)
# MTU = 1500bytes
# max size of MTU header + data = 1472 bytes
    #MTU header =
    #UDP header = 8 bytes
    #IP header = 20 bytes
def create_packet(data, seqNum):
# Two types of packets, data and ack
    #MTU header has the following fields - type, seqNum, length, checksum (4 bytes)
    #MTP header + data gets encapsulated in UDP header (UDP header gets added automatically by the socket -> don't need to implement)
# crc32 available through zlib library
    #after adding the first 3 fields of MTP data and header, sender calculates a 32-bit checksum and appends it to the packet

    packet_type = DATA
    length = len(data)

    #print('data: ', data, ', seqNum: ', seqNum)
    packet = ''
    intermediate = ''
    intermediate = str(packet_type) + str(seqNum) + str(length) + str(data)
    intermediate = str.encode(intermediate)
    checksum = zlib.crc32(intermediate)
    packet = intermediate + bytes(checksum)
    print('checksum:', checksum)

    return packet

def extract_packet_info():
    print("do sth here")
# extract the packet data after receiving


def receive_thread():
    print('do sth here')
	# while True:
		# receive packet, but using our unreliable channel
		# packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
		# call extract_packet_info
		# check for corruption, take steps accordingly
		# update window size, timer, triple dup acks


def main():
    print('hey')
	# read the command line arguments
    recv_ip = sys.argv[1]
    recv_port = sys.argv[2]
    wind_size = sys.argv[3]
    #filename = sys.argv[4]
    filename = './1MB.txt'
    log_filename = sys.argv[5]

	# open log file and start logging
    #logfile = open(log_filename, "a")

	# open client socket and bind  - 'client opens up a UDP client socket'

	# start receive thread
	#recv_thread = threading.Thread(target=rec_thread,args=(client_socket,))
	#recv_thread.start()


	# take the input file and split it into packets (use create_packet)
        #packet data size has to be <= 1472bytes (1472 chars) minus size of header
        #header = 8 bytes unsigned int (type) + 8 bytes unsigned int (seqnum) + 8 bytes unsigned int (length) + checksum (4 bytes)
        #packet data size <= 1472 bytes - 28 bytes = 1444 bytes
    seqNum = 0
    #input_file = open('/home/laura/Downloads/1MB.txt') #open arg4
    input_file = open(filename)
    # print(input_file)
    str = ''
    for line in input_file:
        str += line
    bytes_arr = bytes(str, 'utf-8')
    # print('bytes_arr: ', bytes_arr)
    data = ''
    data_size = 1444
    packets = []
    while(len(bytes_arr)>0):
        data = bytes_arr[0:data_size]
        bytes_arr = bytes_arr[data_size:]
        packet = create_packet(data,seqNum)
        seqNum+=1
        packets.append(packet)

	# while there are packets to send:
		# send packets to server using our unreliable_channel.send_packet()
    #for pckt in packets:

		# update the window size, timer, etc.

main()
