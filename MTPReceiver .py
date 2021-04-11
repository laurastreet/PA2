import unreliable_channel
from socket import *
import sys
import threading
import time
import zlib
DATA = 0
ACK = 1

# channelLock = threading.Semaphore(5)
receiveLock = threading.Semaphore(1)	#start with receive_thread
sendLock = threading.Semaphore(0)

logfile = open("new_logfile.txt", 'w')
output_file = open("output.txt", 'w')
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
    str_type = 'DATA' if packet_type == 0 or packet_type == 2 else 'ACK'
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
    decoded_packet = ModifiedMessage.decode('utf-8')
    # print('decoded_packet: ', decoded_packet)
    end_seqNum = decoded_packet.find('1400')

    packet_type = decoded_packet[0:1]
    str_type = 'DATA' if packet_type == 0 or packet_type == 2 else 'ACK'
    lastPacket = True if packet_type == 2 else False
    seq_num = decoded_packet[1:end_seqNum]
    seq_num = int(seq_num)
    length = decoded_packet[end_seqNum:end_seqNum+4]
    # print('length: ', length)
    data = decoded_packet[end_seqNum+4:end_seqNum+1404]
    # print('data: ', data)
    checksum = decoded_packet[end_seqNum+1404:]
    bytes_arr = bytes(str(packet_type) + str(seq_num) + str(length) + str(data), 'utf-8')
    checksum_calc, corrupt = check_for_corruption(bytes_arr, checksum)
    status = 'NOT_CORRUPT' if not corrupt else 'CORRUPT'
    global logfile
    print('Packet received; type=', str_type, '; seqNum=', seq_num, '; length=', len, '; checksum_in_packet=',
          checksum, '; checksum_calculated=',
          checksum_calc, 'status=', status, file=logfile)
    return seq_num, corrupt, checksum, data, lastPacket
# extract the packet data after receiving

def check_for_corruption(bytes_arr, checksum_sender):
    checksum_calc = zlib.crc32(bytes_arr)				#returns an integer
    checksum_calc = str(checksum_calc)
    # print('checksum: ', checksum)
    if(checksum_calc == checksum_sender):
        return checksum_calc, False
    else:
        return checksum_calc, True

def receiver_thread(receiverSocket,output_file):
    while True:
        receiveLock.acquire()
        global packetsAvailable
        while(packetsAvailable<5):
            global threadlock
            threadlock.acquire()
            packet, serverAddress = receiverSocket.recvfrom(2048)  # modifiedMessage contains packet data - 2048 is the buffer size
            packetsAvailable+=1
            seq_num, corrupt,checksum, data = extract_packet_info(packet)
            output_file.write(data)             #write data to output_file
            print('packet: ', seq_num, ' received, corrupt ', corrupt, ', checksum: ', checksum)
            # time.sleep(2)
            if lastPacket == True:
                threadlock.release()
                break
            threadlock.release()
        sendLock.release()  # increment sendLock so it can send ACKs



#sends ACK for last correctly received packet
def sender_thread(socket,serverAddr,serverPort):
    while True:
        sendLock.acquire()				#this will initially be blocked until packets have been received by receive_thread
        global packetsAvailable
        while (packetsAvailable > 0):
            global threadlock
            threadlock.acquire()
            global ACKsent
            packet, checksum = create_packet(ACKsent)  # ACKsent = seqNum
            socket.sendto(packet, (serverAddr, serverPort))
            # sentlock.release()
            print('ACK: ', ACKsent, 'sent, checksum ', checksum)
            # time.sleep(2)
            ACKsent += 1
            packetsAvailable -= 1
            threadlock.release()
        receiveLock.release()  # increment receiveLock so it can receive more packets

def MTPReceiver_main(arg):
    print('MTPReceiver starting')
    expected_seqNum = 0
    # read the command line arguments
    # receiver_port = sys.argv[1]			#49152
    # output_filename = sys.argv[2]		#received data gets stored here - "output.txt"
    # log_filename = sys.argv[3]		#new_logfile.txt

    # open log file and start logging
    output_filename = "output_file.txt"
    log_filename = 'receiver_log.txt'

    # open log file and start logging
    global logfile
    logfile = open(log_filename, "w")
    output_file = open(output_filename, "w")

    #set up sockets
    receiverAddr = '192.168.1.14'
    serverAddr = '192.168.1.15'
    receiverPort = 49152
    serverPort = 50000
    receiverSocket = socket(AF_INET, SOCK_DGRAM)


    receiverSocket.bind((receiverAddr,receiverPort))
    print('socket bound - MTPReceiver')
    # receiverSocket.settimeout(5)  # 5s timeout (change to 500ms later)
    sendingSocket = socket(AF_INET, SOCK_DGRAM)

    #create threads and start
    senderThread = threading.Thread(target=sender_thread, args=(sendingSocket, serverAddr, serverPort,))
    receiverThread = threading.Thread(target=receiver_thread, args=(receiverSocket,output_file,))

    receiverThread.start()
    senderThread.start()

MTPReceiver_main(0)