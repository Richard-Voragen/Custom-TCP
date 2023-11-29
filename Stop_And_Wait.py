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
    udp_socket.bind(("0.0.0.0", 5000))
    udp_socket.settimeout(1)
    
    # start sending data from 0th sequence
    seq_id = 0
    delays_per_packet = []
    StartThroughputTime = time.time()
    while seq_id < len(data):
        
        # create messages
        seq_id_tmp = seq_id

        # construct messages
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id_tmp, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id_tmp : seq_id_tmp + MESSAGE_SIZE]

        udp_socket.sendto(message, ('localhost', 5001))
        startTime = time.time()

        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            delays_per_packet.append(time.time() - startTime)
        except:
            print("Packet Rejected")
            udp_socket.sendto(message, ('localhost', 5001))

        seq_id += MESSAGE_SIZE
        
    # send final closing message
    udp_socket.sendto(int.to_bytes(-1, 4, signed=True, byteorder='big'), ('localhost', 5001))
    totalTime = (time.time() - StartThroughputTime)

    #print("Total time was : " + totalTime.__str__())
    #print("Total amount of packets : " + (len(acks)-WINDOW_SIZE).__str__())
    print("Average delay per packet was : " + (totalTime/(len(acks)-WINDOW_SIZE)).__str__() + " seconds")
    print("Throughput was : " + (len(data)/totalTime).__str__() + " bytes per second")