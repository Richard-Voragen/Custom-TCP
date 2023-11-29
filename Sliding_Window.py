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
def send_next_message(seq_id, acks):
    temp_id = seq_id + (WINDOW_SIZE * MESSAGE_SIZE)
    acks[temp_id] = False
    if ((seq_id + (WINDOW_SIZE * MESSAGE_SIZE)) < len(data)):
        message = int.to_bytes(temp_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[temp_id : temp_id + MESSAGE_SIZE]

        udp_socket.sendto(message, ('localhost', 5001))
    return (seq_id + MESSAGE_SIZE, acks)

#resends the message at seq_id
def resend_message(seq_id):
    message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id : seq_id + MESSAGE_SIZE]
    udp_socket.sendto(message, ('localhost', 5001))

def send_initial_messages():
    seq_id_tmp = 0
    acks = {}
    messages = []
    for i in range(WINDOW_SIZE):
        # construct messages
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp : seq_id_tmp + MESSAGE_SIZE]
        messages.append((seq_id_tmp, message))
        acks[seq_id_tmp] = False
        # move seq_id tmp pointer ahead
        seq_id_tmp += MESSAGE_SIZE

    # send messages
    for sid, message in messages:
        udp_socket.sendto(message, ('localhost', 5001))

    return (acks)

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    StartThroughputTime = time.time()
    acks = {}
    fast_retransmit = 0

    acks = send_initial_messages()
    while seq_id < len(data):        
        try:
            # wait for ack
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            
            # extract ack id
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            acks[ack_id] = True
            
            if (ack_id != seq_id):
                fast_retransmit += 1
            if (fast_retransmit == 3):
                resend_message(seq_id)
                fast_retransmit = 0

            while (acks[seq_id]):
                seq_id, acks = send_next_message(seq_id, acks)
                fast_retransmit = 0
        except socket.timeout:
            # no ack received, resend unacked message
            fast_retransmit = 0
            resend_message(seq_id)

    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    totalTime = (time.time() - StartThroughputTime)

    #print("Total time was : " + totalTime.__str__())
    #print("Total amount of packets : " + (len(acks)-WINDOW_SIZE).__str__())
    print("Average delay per packet was : " + (totalTime/(len(acks)-WINDOW_SIZE)).__str__() + " seconds")
    print("Throughput was : " + (len(data)/totalTime).__str__() + " bytes per second")