import socket
import time

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

# read data
with open('send.txt', 'rb') as f:
    data = f.read()
 
# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    # bind the socket to a OS port
    udp_socket.bind(("0.0.0.0", 5002))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    StartThroughputTime = time.time()
    while seq_id < len(data):
        
        # create messages
        seq_id_tmp = seq_id

        # construct messages
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp : seq_id_tmp + MESSAGE_SIZE]

        udp_socket.sendto(message, ('localhost', 5001))

        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')
            print(ack_id/1020)
        except:
            print("Packet Rejected")
            udp_socket.sendto(message, ('localhost', 5001))

        seq_id += MESSAGE_SIZE
        
    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    totalTime = (time.time() - StartThroughputTime)
    totalPackages = int(len(data)/MESSAGE_SIZE) + (len(data) % MESSAGE_SIZE > 0)

    #print("Total time was : " + totalTime.__str__())
    #print("Total amount of packets : " + (len(data)/MESSAGE_SIZE).__str__())
    print("Average delay per packet was : " + (totalTime/totalPackages).__str__() + " seconds")
    print("Throughput was : " + (len(data)/totalTime).__str__() + " bytes per second")