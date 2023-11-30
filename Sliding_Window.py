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
WINDOW_SIZE = 100

# read data
with open('send.txt', 'rb') as f:
    data = f.read()

#sends out the next message
def send_next_message(seq_id):
    temp_id = seq_id + (WINDOW_SIZE * MESSAGE_SIZE)
    if ((seq_id + (WINDOW_SIZE * MESSAGE_SIZE)) < len(data)):
        message = int.to_bytes(temp_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[temp_id : temp_id + MESSAGE_SIZE]
        udp_socket.sendto(message, ('localhost', 5001))
    return (seq_id + MESSAGE_SIZE)

#resends the message at seq_id
def resend_message(seq_id):
    message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id : seq_id + MESSAGE_SIZE]
    udp_socket.sendto(message, ('localhost', 5001))

def send_initial_messages():
    seq_id_tmp = 0
    messages = []
    for i in range(WINDOW_SIZE):
        # construct messages
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp : seq_id_tmp + MESSAGE_SIZE]
        messages.append((seq_id_tmp, message))
        # move seq_id tmp pointer ahead
        seq_id_tmp += MESSAGE_SIZE

    # send messages
    for sid, message in messages:
        udp_socket.sendto(message, ('localhost', 5001))

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    StartThroughputTime = time.time()
    fast_retransmit = 0

    send_initial_messages()
    while seq_id < len(data):        
        try:
            # wait for ack
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            
            # extract ack id
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            
            if (ack_id == seq_id):
                fast_retransmit += 1
                if (fast_retransmit == 3):
                    #print("Fast Retransmit")
                    resend_message(seq_id)
                    fast_retransmit = 0
                elif (seq_id + MESSAGE_SIZE > len(data)):
                    break
            else:
                fast_retransmit = 0
                while (seq_id < ack_id):
                    seq_id = send_next_message(seq_id)

        except socket.timeout:
            # no ack received, resend unacked message
            #print("Socket Timeout")
            fast_retransmit = 0
            resend_message(seq_id)
        if (seq_id + MESSAGE_SIZE > len(data)):
            break

    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    totalTime = (time.time() - StartThroughputTime)
    totalPackages = int(len(data)/MESSAGE_SIZE) + (len(data) % MESSAGE_SIZE > 0)

    #print("Total time was : " + totalTime.__str__())
    #print("Total amount of packets : " + totalPackages.__str__())
    print("Average delay per packet was : " + (totalTime/totalPackages).__str__() + " seconds")
    print("Throughput was : " + (len(data)/totalTime).__str__() + " bytes per second")