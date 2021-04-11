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
lowest_unACKed_packet = 0 #critical value
last_ACK_num = null
num_duplicates = 0
## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.

# client_port


## we will need a lock to protect against concurrent threads
#NOTE - you cannot receive and send at the same time
recv_lock = threading.RLock()    #re-entrant lock receiving thread
send_lock = threading.RLock()    #re-entrant lock sending thread

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
    bytes_arr = bytes(str(packet_type) + str(seqNum) + str(length) + str(data.decode()), 'utf-8')
    # print('sizeof(bytes_arr): ', sys.getsizeof(bytes_arr))
    checksum = zlib.crc32(bytes_arr)
    checksum = str(checksum)
    packet = bytes(str(packet_type) + str(seqNum) + str(length) + str(data.decode()) + checksum, 'utf-8')
    # print('packet: ', packet)
    # x = str(packet_type) + str(seqNum) + str(length) + str(data) + checksum
    # print('x: ', x)
    # print('sizeof(checksum): ', sys.getsizeof(checksum))
    # print(type(checksum))
    # print('checksum:', checksum)

    return packet
def log_packet_info(sent_packet):

    decoded_packet = packet_from_server.decode('utf-8')
    packet_type = decoded_packet[0:1]
    str_type = 'DATA' if packet_type == 0 else 'ACK'
    end_seqNum = decoded_packet.find('0x')
    seq_num = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
    len = decoded_packet[end_seqNum + 2:end_seqNum + 3]  # leave out '0x' at beginning of length

    checksum = decoded_packet[end_seqNum + 3:]
    checksum = int(checksum)
    print('Packet sent; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum=', checksum, file=logfile)


def extract_packet_info(packet_from_server):
    decoded_packet = packet_from_server.decode('utf-8')
    packet_type = decoded_packet[0:1]
    #print('packet type: ', packet_type)
    str_type = 'DATA' if packet_type == 0 else 'ACK'
    end_seqNum = decoded_packet.find('0x')
    seq_num = decoded_packet[1:end_seqNum]    ###should be 32 bits/4 bytes
    #print('seq_num: ', seq_num)
    len = decoded_packet[end_seqNum+2:end_seqNum+3]    #leave out '0x' at beginning of length
    #print('len: ', len)
    checksum = decoded_packet[end_seqNum+3:]
    checksum = int(checksum)
    #print('checksum:  ', checksum)
    bytes_arr = bytes(str(packet_type) + str(seq_num) + '0x0', 'utf-8')
    checksum_calculated , corrupt = check_for_corruption(bytes_arr,checksum)
    #print('corrupt: ', corrupt)
    status = 'NOT_CORRUPT' if not corrupt else 'CORRUPT'
    #log the packet data

    print('Packet received; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum_in_packet=',
          checksum,'; checksum_calculated=',
          checksum_calculated, 'status=', status,  file=logfile)
# extract the packet data after receiving
    return seq_num,corrupt

def check_for_corruption(bytes_arr,checksum_sender):
    checksum = zlib.crc32(bytes_arr)
    print('checksum: ', checksum)
    if(checksum==checksum_sender):
        return checksum, False
    else:
        return checksum, True


#where the receive_thread operates
#has to acquire_lock, then release_lock when finished - or use with_lock:
def receive_thread(socket):
    lowest_unACKed_packet = 0
    end_window = lowest_unACKed_packet + 5  # 5 = wind_size
    while(True):
        recv_lock.acquire()
        print('receiver thread starting')
        while(lowest_unACKed_packet<end_window):
            # receive packet, but using our unreliable channel
            # packet_from_server, server_addr = unreliable_channel.recv_packet(socket)
            packet_from_server,server_addr = socket.recvfrom(2048)
            print('serverAddress: ', server_addr)
            seqNum,corrupt = extract_packet_info(packet_from_server)
            # check for corruption, take steps accordingly
            if(not corrupt):
                # update window size, timer, triple dup acks
                #check if a duplicate ack
                if last_ACK_num != null:
                    if seqNum == last_ACK_num:
                       num_duplicates += 1
                    else:
                        num_duplicates = 0
                        last_ACK_num = seqNum
                    if num_duplicates == 3:
                        #resend the oldest unacked packet and start the timer
                        send_pacekt()
                    else:
                        if seqNum == lowest_unACKed_packet:
                            lowest_unACKed_packet +=1
                else:
                    last_ACK_num = seqNum
                    if seqNum == lowest_unACKed_packet:
                        lowest_unACKed_packet += 1
        end_window+=5                           #increment end_window
        recv_lock.release()
        time.sleep(10)

def getSequence(packet):
    decoded_packet = packet.decode('utf-8')
    end_seqNum = decoded_packet.find('1400')
    seq_num = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
    seq_num = int(seq_num)
    return seq_num

def MTPSender_main(arg):
    print('MTPSender starting')
    lowest_unACKed_seq_num = 0
    # read the command line arguments
    # recv_ip = sys.argv[1]
    # recv_port = sys.argv[2]
    # wind_size = sys.argv[3]       #size of sliding window
    wind_size = 5
    # filename = sys.argv[4]        #filename = './1MB.txt'
    filename = '/home/laura/Downloads/1MB.txt'
    #log_filename = sys.argv[5]
    log_filename = 'sender-log-file'

    # open log file and start logging
    logfile = open(log_filename, "w")

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
    recv_thread = threading.Thread(target=receive_thread,args=(receiverSocket,))
    recv_lock.acquire()  # sender acquires receiver's lock
    recv_thread.start()


    # take the input file and split it into packets (use create_packet)
        #packet data size has to be <= 1472bytes (1472 chars) minus size of header
        #header = 8 bytes unsigned int (type) + 8 bytes unsigned int (seqnum) + 8 bytes unsigned int (length) + checksum (4 bytes)
        #packet data size <= 1472 bytes - 28 bytes = 1444 bytes
    input_file = open(filename) #open arg4

        #preprocess entire input file 1st
    str = ''
    for line in input_file:
        str += line
    bytes_arr = bytes(str, 'utf-8')
    # print('sys.getsizeof(bytes_arr): ', sys.getsizeof(bytes_arr))
    data_size = 1400
    packets = []
    lowest_unACKed_packet = 0
    highest_unACKed_packet = 4

    packet_num = 0
    while(len(bytes_arr)>0):
        data = bytes_arr[0:data_size]
        bytes_arr = bytes_arr[data_size:]
        # print('sys.getsizeof(bytes_arr): ', sys.getsizeof(bytes_arr))
        packet = create_packet(data,packet_num)
        packets.append(packet)      #buffer
        packet_num+=1
        # clientSocket.sendto(packet,serverName)

    #sender thread will loop here
    seqNum = 0
    end_window = seqNum + wind_size
    while(len(packets)>0):
        print('end_window: ', end_window)
        while(seqNum<end_window): #send as many packets as equals wind_size
            # send packets to server using our unreliable_channel.send_packet()
            packet = packets.pop(0)
            seqNum = getSequence(packet)
            # print('len(packets): ', len(packets))
            sendingSocket.sendto(packet, (serverAddr, serverPort))  # trial to ensure sockets can communicate
            #print('sent packet: ', seqNum)
            log_packet_info(packet, logfile)
            time.sleep(4)
            seqNum += 1
            # unreliable_channel.send_packet(clientSocket,packet,recv_port)    #last argument is an open port - 631
            # update the window size, timer, etc.
        end_window += wind_size
        recv_lock.release()
        time.sleep(10)
        recv_lock.acquire()



MTPSender_main(0)

