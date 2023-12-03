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

SSTHRESH = 1000000

# read data
with open('file.mp3', 'rb') as f:
    data = f.read()
    data += (b'\x00'* (MESSAGE_SIZE - (len(data)%MESSAGE_SIZE)))


#sends out the next message for the sliding window
def send_next_message(seq_id):
    temp_id = seq_id + (WINDOW_SIZE * MESSAGE_SIZE)
    if ((seq_id + (WINDOW_SIZE * MESSAGE_SIZE)) < len(data)):
        print("SENT", temp_id/1020)
        message = int.to_bytes(temp_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[temp_id : temp_id + MESSAGE_SIZE]
        udp_socket.sendto(message, ('localhost', 5001))
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
    messages = []

    send_next_message(seq_id)
    WINDOW_SIZE += 1

    print("NEW WINDOW SIZE: ", WINDOW_SIZE)

def reset_window_size():
    global SSTHRESH, WINDOW_SIZE
    SSTHRESH = int(WINDOW_SIZE/2)
    WINDOW_SIZE = 1

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    temp_window_size_adder = 0.0
    StartThroughputTime = time.time()
    fast_retransmit = 0

    increase_window_size(seq_id)
    while seq_id < len(data):        
        try:
            # wait for ack
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            
            # extract ack id
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            print("RECV", ack_id/1020)
            
            if (ack_id == seq_id and WINDOW_SIZE > 4):
                fast_retransmit += 1
                if (fast_retransmit == 3):
                    print("Fast Retransmit")
                    reset_window_size()
                    fast_retransmit = 0
                    resend_message(seq_id)
                elif (seq_id + MESSAGE_SIZE > len(data)):
                    break
            elif (ack_id != seq_id):
                fast_retransmit = 0
                while (seq_id < ack_id):
                    seq_id = send_next_message(seq_id)

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
            print("Socket Timeout")
            reset_window_size()
            resend_message(seq_id)
        if (seq_id + MESSAGE_SIZE >= len(data)):
            break

    # send final closing message
    send_closing_message(seq_id)

    totalTime = (time.time() - StartThroughputTime)
    totalPackages = int(len(data)/MESSAGE_SIZE) + (len(data) % MESSAGE_SIZE > 0)

    #print("Total time was : " + totalTime.__str__())
    #print("Total amount of packets : " + totalPackages.__str__())
    print("Average delay per packet was : " + (totalTime/totalPackages).__str__() + " seconds")
    print("Throughput was : " + (len(data)/totalTime).__str__() + " bytes per second")