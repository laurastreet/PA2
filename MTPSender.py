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
curr_time = 0
#last_ACK_num = null


# channelLock = threading.Semaphore(0)    #start with sender
sendLock = threading.Semaphore(1)
receiveLock = threading.Semaphore(0)

packetsSent = 0
packetIdx = 0
lowestPacketIdx = 0
packetsReceived = 0
prevACKReceived = -1
numDuplicates = 0

threadLock = threading.Lock()
timeLock = threading.Lock()

## define and initialize
# window_size, window_base, next_seq_number, dup_ack_count, etc.

def create_packet(data, seqNum):
    packet_type = DATA
    length = len(data)
    bytes_arr = bytes(str(packet_type) + str(seqNum) + str(length) + str(data.decode()), 'utf-8')
    checksum = zlib.crc32(bytes_arr)
    checksum = str(checksum)
    packet = bytes(str(packet_type) + str(seqNum) + str(length) + str(data.decode()) + checksum, 'utf-8')
    return packet


#log packet received info in this method
def extract_packet_info(packet_from_server,logfile):
    decoded_packet = packet_from_server.decode('utf-8')
    packet_type = decoded_packet[0:1]
    str_type = 'DATA' if packet_type == '0' else 'ACK'
    if(str_type == 'ACK'):
        end_seqNum = decoded_packet.find('0x')
        # print('end_seqNum: ', end_seqNum)
        seq_num = decoded_packet[1:end_seqNum]    ###should be 32 bits/4 bytes
        # print('seq_num: ', seq_num)
        len = decoded_packet[end_seqNum+2:end_seqNum+3]    #leave out '0x' at beginning of length
        # print('len: ', len)
        checksum = decoded_packet[end_seqNum+3:]
        checksum = int(checksum)
        # print('checksum: ', checksum)
        bytes_arr = bytes(str(packet_type) + str(seq_num) + '0x0', 'utf-8')
    checksum_calc, corrupt = check_for_corruption(bytes_arr,checksum)
    # print('checksum_calc: ', checksum_calc)
    status = 'NOT_CORRUPT' if not corrupt else 'CORRUPT'
    print('Packet received; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum_in_packet=',
          str(checksum), '; checksum_calculated=',
          str(checksum_calc), 'status=', status, file=logfile)
    # extract the packet data after receiving
    return seq_num,corrupt, checksum


def log_packet_info(sent_packet,logfile):
    decoded_packet = sent_packet.decode('utf-8')
    # print('decoded_packet: ', decoded_packet)
    packet_type = decoded_packet[0:1]
    print('packet_type: ', packet_type)
    if packet_type == '0':
        str_type = 'DATA'
        end_seqNum = decoded_packet.find('1400')
        # print('end_seqNum:  ', end_seqNum)
        seq_num = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
        # print('seq_num: ', seq_num)
        len = decoded_packet[end_seqNum:end_seqNum + 4]  # len sent_packet = 1400
        # data = decoded_packet[end_seqNum+4:end_seqNum+1404]
        checksum = decoded_packet[end_seqNum + 1404:]
        checksum = int(checksum)
        # print('checksum: ', checksum)
    else:
        str_type = 'ACK'
        end_seqNum = decoded_packet.find('0x')
        seq_num = decoded_packet[1:end_seqNum]
        len = decoded_packet[end_seqNum+2:end_seqNum+3] #get rid of '0x'
        checksum = decoded_packet[end_seqNum+3:]    #no data in ACK packet
    # print('\nPacket sent; type=', str_type, '\n; seqNum=', seq_num, '\n; length=', len, '\n; checksum=', checksum,)
    print('Packet sent; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum=', checksum,
          file=logfile)



def check_for_corruption(bytes_arr,checksum_sender):
    checksum = zlib.crc32(bytes_arr)
    # print('checksum: ', checksum)
    if(checksum==checksum_sender):
        return checksum, False
    else:
        return checksum, True


def getPacketSeqNum(packet):
    decoded_packet = packet.decode('utf-8')
    end_seqNum = decoded_packet.find('1400')
    seqNum = decoded_packet[1:end_seqNum]  ###should be 32 bits/4 bytes
    seqNum = int(seqNum)
    return seqNum

def getPacketCheckSum(packet):
    decoded_packet = packet.decode('utf-8')
    end_seqNum = decoded_packet.find('1400')
    len = decoded_packet[end_seqNum:end_seqNum+4]
    data = decoded_packet[end_seqNum+4:end_seqNum+1404]
    checksum = decoded_packet[end_seqNum+1404:]
    return checksum

def send_thread(senderSocket, serverAddr,serverPort, packets, wind_size,logfile):
    ###the sender may have to resend some packets - it should probably iterate through the last 5 packets and ensure that they were properly
    #received - i.e. check their True values - prior to sending packets from a new window
    while True:
        global threadLock
        global packetsSent
        global packetIdx
        #send window sized # packets at a time, then give up lock
        sendLock.acquire()      #initial value is 1 -> can start before receive_thread
        # while(packetsSent<5):
        #first check that previous packets have been sent properly
        while(packetsSent<wind_size):
            threadLock.acquire()
            packet_with_bool = packets[packetIdx]           #idx is the sequence number
            # print('packet_with_bool: ', packet_with_bool)
            packet = packet_with_bool[0]
            senderSocket.sendto(packet, (serverAddr, serverPort))  # trial to ensure sockets can communicate
            log_packet_info(packet,logfile)
            if packetsSent == 0:                     #if seqNum equals oldest unACKed packet
                resetTimer()
            print('packet: ', packetIdx, ' sent, ', 'checksum: ', getPacketCheckSum(packet))
            packetsSent +=1
            packetIdx +=1
            threadLock.release()
        print('packetsSent: ', packetsSent)
        packetsSent = 0             #reset packetsSent to zero
        receiveLock.release()       #release receive_thread after 5 packets sent


def resetTimer():
    global curr_time
    timeLock.acquire()
    curr_time = time.perf_counter()  # start oldest packet timer
    print('curr_timeSEND: ', curr_time)
    timeLock.release()
    # return new_time         ###question about this???? (not defined in this function)

#checks whether 0.5s has elapsed since oldest ACK-ed packet has been sent
def elapsedTimer():
    global curr_time
    timeLock.acquire()
    new_time = time.perf_counter() - curr_time       #this should be <500ms for oldest unACKed packet
    print('curr_timeRECEIVE: ', new_time)
    timeLock.release()
    return new_time




#where the receive_thread operates
#se boolean value to True to indicate that packets have been properly received
def receive_thread(receiverSocket,senderSocket,serverAddr,serverPort,logfile,wind_size):
    while True:
        receiveLock.acquire()       #initial value = 0 -> has to wait until send_thread is finished
        print('in receive_thread')
        global threadLock
        global lowestPacketIdx
        global packetsReceived
        global prevACKReceived
        global numDuplicates

        elapsed_time = 0.0
        #maybe I should recheck the time if it didn't elapse after receiving the lowest unACKed packet, so this doesn't deadlock?
        #(e.g. if only one packet in the window was being resent)
        while(packetsReceived<wind_size and elapsed_time <0.5):
        # while(packetsReceived<5):
            threadLock.acquire()
            # print('lowestPacketIdx: ', lowestPacketIdx)        #lowest unACKed packet
            ACK,serverAddress = receiverSocket.recvfrom(2048)
            seqNum,corrupt,checksum = extract_packet_info(ACK,logfile)
            if(not corrupt and seqNum==lowestPacketIdx):
                elapsed_time = elapsedTimer()
                    #if timeout occurs for oldest unACKed packet
                if(elapsed_time>0.5):           #returns value of time in seconds
                    #resend all packets in window
                    i=0
                    while(i<wind_size and i<len(packets)):            #check for final packet (in this case, can potentially resend fewer packets than wind_size)
                        packet_with_bool = packets[seqNum+i]        #get packet with data
                        packet = packet_with_bool[0]                #packet_with_bool is in format [packet,True/False]
                        senderSocket.sendto(packet,(serverAddr,serverPort))     #resend packet
                        i+=1
                    resetTimer()
                else:
                    packets[seqNum] = True      #I think we only mark this as true if the timer hasn't elapsed (so check that first)

            #check for triple duplicate ACK
            if(not corrupt and seqNum!=0):
                if prevACKReceived == -1:  # if no acks were received before
                    prevACKReceived = seqNum
                else:  # check the previous acks
                    if prevACKReceived == seqNum:
                        numDuplicates += 1
                        if numDuplicates == 3:
                            packet_with_bool = packets[seqNum]
                            packet = packet_with_bool[0]
                            senderSocket.sendto(packet, (serverAddr, serverPort))  #resend packet
                            resetTimer()
                            numDuplicates = 0

            #if ACK is corrupt,  we ignore

            packetsReceived += 1
            print('packet: ', seqNum, ' received, checksum: ', checksum)
            threadLock.release()
        packetsReceived = 0                 #reset packetsReceived = 0
        lowestPacketIdx +=5                       #increase lowest unACKed packet by window size
        sendLock.release()                  #increments value of send_thread semaphore so send_thread can go now


def resendPacket(packet,senderSocket,serverAddr,serverPort,logfile):
        for packet, status in packets:
            if status == False:
                senderSocket.sendto(packet, (serverAddr, serverPort))
                log_packet_info(packet,logfile)
                resetTimer()
            break


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
    # print('recv_port: ', recv_port)
    wind_size = int(sys.argv[3])       #size of sliding window
    # wind_size = 5             wind_size = 5
    # filename = sys.argv[4]        #filename = './1MB.txt'
    filename = '/home/laura/Downloads/1MB.txt'
    # log_filename = sys.argv[5]     #log_filename = sender_log.txt
    log_filename = 'sender_log.txt'

    # open log file and start logging
    global logfile
    logfile = open(log_filename, "w")


    #set up sockets
    serverAddr = '192.168.1.14'
    serverPort = 49152  # receiverPort = 49700
    sendingSocket = socket(AF_INET, SOCK_DGRAM)
    sendingSocket.settimeout(0.5)        #500ms timeout
    receiverSocket = socket(AF_INET, SOCK_DGRAM)        #desktop IP = 192.168.1.15
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

    #add an end-of-sequence indicator to the final packet (change seqNum to "***")
    final_packet_with_bool = packets[len(packets)]
    final_packet = final_packet_with_bool[0]

    seqNum = 0
    #start threads
    senderThread = threading.Thread(target=send_thread,
                                    args=(sendingSocket,serverAddr,serverPort,packets, wind_size,logfile))
    receiverThread = threading.Thread(target=receive_thread,
                                      args=(receiverSocket,sendingSocket,serverAddr,serverPort,logfile, wind_size))
    senderThread.start()
    receiverThread.start()


MTPSender_main(0)

