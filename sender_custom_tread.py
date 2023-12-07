import socket
import time
import threading
import math
from joblib import Parallel, delayed

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

def send_closing_message(seq_id, udp_socket):
    finalMessage = int.to_bytes(seq_id + MESSAGE_SIZE, SEQ_ID_SIZE, byteorder='big', signed=True)
    udp_socket.sendto(finalMessage, ('localhost', 5001))

    closingMessage = int.to_bytes(-1, SEQ_ID_SIZE, byteorder='big', signed=True) + b"==FINACK=="
    udp_socket.sendto(closingMessage, ('localhost', 5001))    

# read data

def send(packet):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

        # bind the socket to a OS port
        udp_socket.bind(("0.0.0.0", threading.get_native_id()))
        udp_socket.settimeout(0.5)
        
        # start sending data from 0th sequence
        seq_id = packet*MESSAGE_SIZE
        StartThroughputTime = time.time()


        print(packet)
        math.ceil(len(data)/MESSAGE_SIZE)

        # construct messages
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id : seq_id + MESSAGE_SIZE]

        udp_socket.sendto(message, ('localhost', 5001))
        per_packet_delay = time.time()

        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            per_packet_delay = time.time() - per_packet_delay
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            print("acked", ack_id/1020)
        except:
            print("Packet Rejected")
            udp_socket.sendto(message, ('localhost', 5001))
        
        return per_packet_delay


with open('file.mp3', 'rb') as f:
    data = f.read()
    data += (b'\x00'* (MESSAGE_SIZE - (len(data)%MESSAGE_SIZE)))


total_data = math.ceil(len(data)/MESSAGE_SIZE)
results = Parallel(n_jobs=5)(delayed(send)(i) for i in range(total_data))

sum = 0
for i in results:
    sum += 1

print(results)
print("Average Packet Delay : ", )