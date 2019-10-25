import socket
import time
import argparse
import random
import struct
import sys
import struct
import random
import asyncore
import select

IMCP_ECHO_REQUEST = 8
IMCP_CODE = socket.getprotobyname('icmp')

def checksum(msg):
    #print('Entered checksum function.')
    s = 0
    count_to = (len(msg) // 2) * 2
    my_count = 0
    while my_count < count_to:
        my_val = (msg[my_count + 1])*256+(msg[my_count])
        s = s + my_val
        s = s & 0xffffffff 
        my_count = my_count + 2
    if count_to < len(msg):
        s = s + (msg[len(msg) - 1])
        s = s & 0xffffffff 
    s = (s >> 16) + (s & 0xffff)
    s = s + (s >> 16)
    answer = ~s
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer
    
def create_icmp_packet(id, payload):
    #Create header using struct with layout bbHHh, containing dummy values
    header = struct.pack('bbHHh', IMCP_ECHO_REQUEST, 0, 0, id, 1)
    data = payload
    data = data.encode('ascii')
    #Calculate checksum on the data and dummy header
    calculate_checksum = checksum(header+data)
    #Create header with real values
    header = struct.pack('bbHHh', IMCP_ECHO_REQUEST, 0, socket.htons(calculate_checksum), id, 1)

    return header + data

def receive_ping(my_socket, packet_id, time_sent, timeout):
    #Receive the ping from the socket
    time_left = timeout

    while True:
        start_time = time.time()
        ready = select.select([my_socket], [], [], time_left)
        time_spent_in_select = time.time() - start_time
        #Check for timeout
        if ready[0] == []: 
            return

        received, addr = my_socket.recvfrom(1024)
        time_received = time.time()
        icmp_header = received[20:28]
        received_type, received_code, received_checksum, received_packet_id, received_sequence = struct.unpack('bbHHh', icmp_header)

        if received_packet_id == packet_id:
            return time_received - time_sent

        time_left -= time_received - time_sent
        if time_left <= 0:
            return

def send_one_ping(dest_addr, payload, timeout = 1):
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, IMCP_CODE)
    except:
        print('Error: Could not create socket.')
        sys.exit()
    
    try:
        my_host = socket.gethostbyname(dest_addr)
    except:
        print('Could not connect to destination address.')
        sys.exit()

    #Ensure that packet id is not greater than 65535, the maximum for unsigned short int c
    packet_id = int((id(timeout) *random.random()) % 65535)
    packet = create_icmp_packet(packet_id, payload)

    while packet:
        #Provide a dummy port, (1)
        sent = my_socket.sendto(packet, (dest_addr, 1))
        packet = packet[sent:]

    delay = receive_ping(my_socket, packet_id, time.time(), timeout)
    my_socket.close()

    return delay

def get_average(array, timeout=5):
    my_sum = 0
    for a in array:
        if a == None:
            my_sum += timeout
        else:
            my_sum += a
    
    my_sum = my_sum/len(array)
    return my_sum

def get_received(array):
    my_sum = 0
    for a in array:
        if not a == None:
            my_sum += 1
    
    return my_sum

def get_missing(array):
    my_sum = 0
    for a in array:
        if a == None:
            my_sum += 1

    return my_sum

def get_maximum(array):
    #Returns -1 if there is no maximum time to find
    my_max = -1

    for a in array:
        if not a == None:
            if a > my_max:
                my_max = a

    return my_max

def get_minimum(array):
    #Returns -1 if there is no minimum time to find
    my_min = array[0]

    for a in array:
        if not a == None:
            if my_min == None:
                my_min = a
            elif a < my_min:
                my_min = a

    if my_min == None:
        my_min = -1

    return my_min

def get_percent_missing(sent, missing):
    my_result = missing/sent
    my_result = round(my_result*100, 4)

    return my_result

def main():
    #Process command line input-------------------------------
    parser = argparse.ArgumentParser()
    arg_group = parser.add_argument_group()
    arg_group.add_argument('-p', '--payload', help = 'Payload to be delivered.')
    arg_group.add_argument('-c', '--count', help = 'Number of packets sent.')
    arg_group.add_argument('-d', '--destination', help = 'Destination of payload.')
    arg_group.add_argument('-l', '--logfile', help = 'Destination of logfile.')
    parser.add_argument('-t', '--timeout', help = "Time for packet to live.")
    args = parser.parse_args()

    if(not len(sys.argv) > 3):
        print("\nCOMMAND LINE INSTRUCTIONS: ")
        print ("-p <payload> indicates the payload")
        print ("-c <count> indicates number of packets sent")
        print ("-l <logfile> name of the logfile")
        print ("-d <destination> indicates destination of payload")
        print ("\nInsufficient arguments, terminating client now.")
        sys.exit()
    else:
        if args.destination:
            DEST_ADDR = args.destination
        else:
            DEST_ADDR = 'localhost'
        if args.logfile:
            LOGFILE = args.logfile
        else:
            LOGFILE = "logfile.txt"
        if args.count:
            COUNT = int(args.count)
        else:
            COUNT = 10
        if args.payload:
            PAYLOAD = args.payload
        else:
            PAYLOAD = "Hello, world."
        if args.timeout:
            TIMEOUT = args.timeout
        else:
            TIMEOUT = 5
        
    #-----------------------------------------------------------
    #Write to logfile
    WRITE_TO_FILE = open(LOGFILE, "a+")

    SRC_IP = 'localhost' #arbitrary and unused host
    SRC_PORT = '8000'  #arbitary and unused port
    DST_PORT = '34567' #arbitrary and unused port



    #-----------------------------------------------------------
    i = 0
    result_array = []
    PAYLOAD_LEN = len(PAYLOAD)
    print('Pinging %s with %s bytes of data "%s"' %(DEST_ADDR, PAYLOAD_LEN, PAYLOAD))
    while(i < COUNT):
        result = send_one_ping(DEST_ADDR, PAYLOAD, TIMEOUT)
        if(result == None):
            print('Packet failed to send. (Timeout within {} seconds.)'.format(TIMEOUT))
            WRITE_TO_FILE.write('\nPacket failed to send. (Timeout within {} seconds.)'.format(TIMEOUT))
        else:
            result = round(result*1000.0, 4)
            print('Reply from %s: bytes=%s time=%sms TTL=%ss' %(DEST_ADDR, COUNT, result, TIMEOUT))
            WRITE_TO_FILE.write('\nReply from %s: bytes=%s time=%s TTL=%sms' %(DEST_ADDR, COUNT, result, TIMEOUT))        
        result_array.append(result)
        i += 1

    RECEIVED = get_received(result_array)
    LOST = get_missing(result_array)
    PERCENT_LOST = get_percent_missing(COUNT, LOST)
    MINIMUM_TIME = get_minimum(result_array)
    MAXIMUM_TIME = get_maximum(result_array)
    AVERAGE_TIME = get_average(result_array, TIMEOUT)

    print('\nPing statistics for %s:'%(DEST_ADDR)) 
    print('\tPackets: Sent = %s, Received = %s, Lost = %s (%s %% loss)' %(COUNT, RECEIVED, LOST, PERCENT_LOST))
    print('Approximate round trip times in milliseconds: ')
    print('\tMinimum = %sms, Maximum = %sms, Average = %s' %(MINIMUM_TIME, MAXIMUM_TIME, AVERAGE_TIME))
    WRITE_TO_FILE.write('\nPing statistics for %s: Packets: Sent = %s, Received = %s, Lost = %s (%s %% loss)' %(DEST_ADDR, COUNT, RECEIVED, LOST, PERCENT_LOST))
    WRITE_TO_FILE.write('\nApproximate round trip times in milliseconds: ')
    WRITE_TO_FILE.write('\nMinimum = %sms, Maximum = %sms, Average = %s' %(MINIMUM_TIME, MAXIMUM_TIME, AVERAGE_TIME))

if __name__ == "__main__":
    main()
