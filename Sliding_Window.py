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
WINDOW_SIZE = 10

# read data
with open('send.txt', 'rb') as f:
    data = f.read()
 
# returns amount to slide and messages with the front items removed
def get_slide_amount(seq_id, messages, acks):
    amount = 0
    tmp_seq_id = seq_id
    try:
        while (acks[tmp_seq_id]):
            amount += 1
            messages.pop(0)
            tmp_seq_id += MESSAGE_SIZE
    except:
        pass
    if (amount > 1):
        print(amount)
    return (amount, messages)

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    StartThroughputTime = time.time()
    delays_per_packet = {}
    slide_amount = WINDOW_SIZE
    while seq_id < len(data)/4:        
        # create messages
        messages = []
        acks = {}
        seq_id_tmp = seq_id + (MESSAGE_SIZE * (WINDOW_SIZE - slide_amount))
        for i in range(slide_amount):
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
            delays_per_packet[sid] = time.time()

        
        # wait for acknowledgement
        while True:
            try:
                # wait for ack
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                
                # extract ack id
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
                #print(ack_id, ack[SEQ_ID_SIZE:])
                acks[ack_id] = True
                delays_per_packet[ack_id] = time.time() - delays_per_packet[ack_id]
                
                # all acks received, move on
                if acks[seq_id]:
                    break
            except socket.timeout:
                # no ack received, resend unacked messages
                print("timeout")
                for sid, message in messages:
                    if not acks[sid]:
                        udp_socket.sendto(message, ('localhost', 5001))
                
        # move sequence id forward
        slide_amt, messages = get_slide_amount(seq_id, messages, acks)
        seq_id += MESSAGE_SIZE * slide_amt
        
    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    totalTime = (time.time() - StartThroughputTime)

    print("Average delay per packet was : " + (sum(delays_per_packet.values())/len(delays_per_packet.values())).__str__() + " seconds")
    print("Total amount of packets : " + len(delays_per_packet.values()).__str__())
    print("Total time was : " + totalTime.__str__())
    print("Throughput was : " + (len(data)/totalTime).__str__() + "bytes per second")