## The code provided here is just a skeleton that can help you get started
## You can add/remove functions as you wish

## import (add more if you need)
import unreliable_channel
from socket import *
DATA = 0
ACK = 1

def create_packet():
	print('do sth here')
# Two types of packets, data and ack
    # ACK packet header has the following fields - type, seqNum, length, checksum
# crc32 available through zlib library


def extract_packet_info():
	print('do sth here')
# extract the packet data after receiving


def main():
	# read the command line arguments

	# open log file and start logging

	# open server socket and bind - 'receiver opens up a UDP server socket'

	while True:
		# receive packet, but using our unreliable channel

		# call extract_packet_info

		# check for corruption and lost packets, send ack accordingly


