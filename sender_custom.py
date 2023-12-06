import socket
from datetime import datetime
import time

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
# total packets to send
WINDOW_SIZE = 0

SSTHRESH = 100000

# read data
with open('file.mp3', 'rb') as f:
    data = f.read()
    data += (b'\x00'* (MESSAGE_SIZE - (len(data)%MESSAGE_SIZE)))


def get_initial_time(seq_id):
    global per_packet_delay
    max = 0
    for i in range(10):
        try:
            # wait for ack
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            per_packet_delay[seq_id] = time.perf_counter() - per_packet_delay[seq_id]
            if (per_packet_delay[seq_id] > max):
                max = per_packet_delay[seq_id]
            seq_id = send_next_message(seq_id)
        except socket.timeout:
            # no ack received, resend unacked message
            #print("Socket Timeout")
            resend_message(seq_id)
    max *= 1.25
    #print(max)
    return seq_id, max


#sends out the next message for the sliding window
def send_next_message(seq_id):
    global per_packet_delay

    temp_id = seq_id + (WINDOW_SIZE * MESSAGE_SIZE)
    if ((seq_id + (WINDOW_SIZE * MESSAGE_SIZE)) < len(data)):
        #print("SENT", temp_id/1020)
        message = int.to_bytes(temp_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[temp_id : temp_id + MESSAGE_SIZE]
        udp_socket.sendto(message, ('localhost', 5001))

        per_packet_delay[temp_id] = time.perf_counter()
    return (seq_id + MESSAGE_SIZE)

#resends the message at seq_id
def resend_message(seq_id):
    message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id : seq_id + MESSAGE_SIZE]
    udp_socket.sendto(message, ('localhost', 5001))

def send_closing_message(seq_id):
    finalMessage = int.to_bytes(seq_id + MESSAGE_SIZE, SEQ_ID_SIZE, byteorder='big', signed=True)
    udp_socket.sendto(finalMessage, ('localhost', 5001))

    closingMessage = int.to_bytes(-1, SEQ_ID_SIZE, byteorder='big', signed=True) + b"==FINACK=="
    udp_socket.sendto(closingMessage, ('localhost', 5001))    

def increase_window_size(seq_id):
    global WINDOW_SIZE

    send_next_message(seq_id)
    WINDOW_SIZE += 1

    #print("NEW WINDOW SIZE: ", WINDOW_SIZE)

def reset_window_size():
    global SSTHRESH, WINDOW_SIZE, waitTime
    SSTHRESH = max(20, WINDOW_SIZE)
    WINDOW_SIZE = int(WINDOW_SIZE/2)
    waitTime = time.perf_counter()

waitTime = time.perf_counter()
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    temp_window_size_adder = 0.0
    StartThroughputTime = time.perf_counter()
    fast_retransmit = 0

    per_packet_delay = {}
    delay = 0.25

    increase_window_size(seq_id)
    seq_id, delay = get_initial_time(seq_id)
    while seq_id < len(data):        
        try:
            # wait for ack
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            
            # extract ack id
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            #print("RECV", ack_id/1020)
            
            if (ack_id == seq_id and (time.perf_counter()-waitTime) > 2):
                fast_retransmit += 1
                if (fast_retransmit == 3):
                    #print("Fast Retransmit")
                    reset_window_size()
                    fast_retransmit = 0
                    resend_message(seq_id)
                elif (seq_id + MESSAGE_SIZE > len(data)):
                    break
            elif (ack_id != seq_id):
                fast_retransmit = 0
                while (seq_id < ack_id):
                    per_packet_delay[seq_id] = time.perf_counter() - per_packet_delay[seq_id]
                    seq_id = send_next_message(seq_id)
                if per_packet_delay[seq_id-MESSAGE_SIZE] > delay:
                    reset_window_size()

            if (WINDOW_SIZE > SSTHRESH):
                temp_window_size_adder += 1/WINDOW_SIZE
                if temp_window_size_adder >= 1:
                    increase_window_size(seq_id)
                    temp_window_size_adder -= 1.0
            else:
                increase_window_size(seq_id)

        except socket.timeout:
            # no ack received, resend unacked message
            fast_retransmit = 0
            #print("Socket Timeout")
            reset_window_size()
            resend_message(seq_id)
        if (seq_id + MESSAGE_SIZE >= len(data)):
            break

    # send final closing message
    send_closing_message(seq_id)

    totalTime = (time.perf_counter() - StartThroughputTime)
    totalPackages = int(len(data)/MESSAGE_SIZE) + (len(data) % MESSAGE_SIZE > 0)

    per_packet_delay.popitem()
    total = 0.0
    count = 0
    for value in per_packet_delay.values():
        total += value
        count += 1

    #print("Total time was : " + totalTime.__str__())
    #print("Total amount of packets : " + totalPackages.__str__())
    print(round(len(data)/totalTime, 2).__str__() + ",")
    print(round(total/count, 2).__str__() + ",")
    print(round((len(data)/totalTime)/(total/count), 2).__str__())