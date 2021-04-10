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
packets = []

channelLock = threading.Semaphore(5)    #argument will be window_size
packetsSent = 0
packetsReceived = 0
sentLock = threading.Lock()
receivedLock = threading.Lock()
## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.

# client_port


## we will need a lock to protect against concurrent threads
#NOTE - you cannot receive and send at the same time
recv_lock = threading.RLock()    #re-entrant lock receiving thread

# take the input file and split it into packets (use create_packet)
# MTU = 1500bytes
def create_packet(data, seqNum):
    #after adding the first 3 fields of MTP data and header, sender calculates a 32-bit checksum and appends it to the packet
    packet_type = DATA
    length = len(data)
    bytes_arr = bytes(str(packet_type) + str(seqNum) + str(length) + str(data.decode()), 'utf-8')
    checksum = zlib.crc32(bytes_arr)
    checksum = str(checksum)
    packet = bytes(str(packet_type) + str(seqNum) + str(length) + str(data.decode()) + checksum, 'utf-8')
    return packet

def extract_packet_info(packet_from_server):
    decoded_packet = packet_from_server.decode('utf-8')
    packet_type = decoded_packet[0:1]
    end_seqNum = decoded_packet.find('0x')
    seq_num = decoded_packet[1:end_seqNum]    ###should be 32 bits/4 bytes
    seq_num = int(seq_num)
    len = decoded_packet[end_seqNum+2:end_seqNum+3]    #leave out '0x' at beginning of length
    checksum = decoded_packet[end_seqNum+3:]
    checksum = int(checksum)
    bytes_arr = bytes(str(packet_type) + str(seq_num) + '0x0', 'utf-8')
    corrupt = check_for_corruption(bytes_arr,checksum)
# extract the packet data after receiving
    return seq_num,corrupt

def check_for_corruption(bytes_arr,checksum_sender):
    checksum = zlib.crc32(bytes_arr)
    print('checksum: ', checksum)
    if(checksum==checksum_sender):
        return False
    else:
        return True

def getPacketSeqNum(packet):
    decoded_packet = packet.decode('utf-8')
    end_seqNum = decoded_packet.find('1400')
    seqNum = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
    seqNum = int(seqNum)
    return seqNum

def send_thread(senderSocket, serverAddr,serverPort,packets):
    while True:
        channelLock.acquire()
        global sentLock
        sentLock.acquire()
        packet_with_bool = packets.pop(0)
        # print('packet_with_bool: ', packet_with_bool)
        packet = packet_with_bool[0]
        senderSocket.sendto(packet, (serverAddr, serverPort))  # trial to ensure sockets can communicate
        seqNum = getPacketSeqNum(packet)
        global packetsSent
        packetsSent +=1
        sentLock.release()
        print('packet: ', seqNum, ' sent')

#where the receive_thread operates
#has to acquire_lock, then release_lock when finished - or use with_lock:
####set the boolean values in packets to True if timeout occurs (otherwise, leave as False)
####or, can set them to True to indicate that they have been properly received - this is probably better design
def receive_thread(receiverSocket):
    while True:
        channelLock.release()
        global receivedLock
        receivedLock.acquire()
        packet,serverAddress = receiverSocket.recvfrom(2048)
        seqNum,corrupt = extract_packet_info(packet)
        global packetsReceived
        packetsReceived += 1
        receivedLock.release()
        print('packet: ', seqNum, ' received')

def getPacketInfo(packet):
    decoded_packet = packet.decode('utf-8')
    end_seqNum = decoded_packet.find('1400')
    seq_num = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
    seq_num = int(seq_num)
    checksum = decoded_packet[end_seqNum+1404:]
    return seq_num,checksum

def MTPSender_main(arg):
    # read the command line arguments
    recv_ip = sys.argv[1]           #receiverAddr = '192.168.1.15'
    recv_port = int(sys.argv[2])         #receiverPort = 49153
    print('recv_port: ', recv_port)
    wind_size = int(sys.argv[3])       #size of sliding window
    # wind_size = 5             wind_size = 5
    # filename = sys.argv[4]        #filename = './1MB.txt'
    filename = '/home/laura/Downloads/1MB.txt'
    # log_filename = sys.argv[5]     #log_filename = sender_log.txt
    log_filename = 'sender_log.log'

    # open log file and start logging
    logfile = open(log_filename, "a")
    # logging.basicConfig(filename=log_filename,encoding='utf-8', level=logging.DEBUG)

    #set up sockets
    # serverAddr = '192.168.1.14'
    serverAddr = '172.20.10.5'      #address of laptop
    # receiverAddr = '192.168.1.15'     #address of desktop
    serverPort = 49152
    # receiverPort = 49700
    sendingSocket = socket(AF_INET, SOCK_DGRAM)
    sendingSocket.settimeout(0.5)        #500ms timeout
    receiverSocket = socket(AF_INET, SOCK_DGRAM)
    receiverSocket.bind((recv_ip,recv_port))


    #preprocess input file into packets
    input_file = open('/home/laura/Downloads/1MB.txt') #open arg4
    str = ''
    for line in input_file:
        str += line
    bytes_arr = bytes(str, 'utf-8')
    data_size = 1400

    packet_num = 0
    while(len(bytes_arr)>0):
        data = bytes_arr[0:data_size]
        bytes_arr = bytes_arr[data_size:]
        packet = create_packet(data,packet_num)
        packets.append([packet,False])      #buffer
        # packets.append(packet)
        packet_num+=1

    #start threads
    senderThread = threading.Thread(target=send_thread,args=(sendingSocket,serverAddr,serverPort,packets))
    receiverThread = threading.Thread(target=receive_thread, args=(receiverSocket,))
    senderThread.start()
    receiverThread.start()


MTPSender_main(0)

