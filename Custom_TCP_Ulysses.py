import socket
import time
import threading

PACKET_SIZE = 1024
SEQ_ID_SIZE = 4
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE
WINDOW_SIZE = 1
SSTHRESH = 64

stop_thread = False

with open('docker/file.mp3', 'rb') as f:
    data = f.read()
    data += (b'\x00' * (MESSAGE_SIZE - (len(data) % MESSAGE_SIZE)))

def send_message(seq_id):
    global per_packet_delay
    if seq_id < len(data):
        message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id: seq_id + MESSAGE_SIZE]
        per_packet_delay[seq_id] = time.time()
        udp_socket.sendto(message, ('localhost', 5001))
    return seq_id + MESSAGE_SIZE

def resend_message(seq_id):
    message = int.to_bytes(seq_id, SEQ_ID_SIZE, byteorder='big', signed=True) + data[seq_id: seq_id + MESSAGE_SIZE]
    udp_socket.sendto(message, ('localhost', 5001))

def send_closing_message(seq_id):
    final_message = int.to_bytes(seq_id + MESSAGE_SIZE, SEQ_ID_SIZE, byteorder='big', signed=True)
    udp_socket.sendto(final_message, ('localhost', 5001))
    closing_message = int.to_bytes(-1, SEQ_ID_SIZE, byteorder='big', signed=True) + b"==FINACK=="
    udp_socket.sendto(closing_message, ('localhost', 5001))

def reset_window_size():
    global SSTHRESH, WINDOW_SIZE
    SSTHRESH = max(2, int(WINDOW_SIZE / 2))
    WINDOW_SIZE = 1

def send_window_size(seq_id):
    global WINDOW_SIZE
    temp_id = seq_id
    for _ in range(WINDOW_SIZE):
        temp_id = send_message(temp_id)
    return temp_id

def ack_receiver():
    global seq_id, max_seq_id, fast_retransmit, WINDOW_SIZE, SSTHRESH, stop_thread
    while not stop_thread:
        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')

            if ack_id == seq_id:
                fast_retransmit += 1
                if fast_retransmit == 2:
                    reset_window_size()
                    fast_retransmit = 0
                    resend_message(seq_id)
                elif seq_id + MESSAGE_SIZE > len(data):
                    break
            elif ack_id != seq_id:
                fast_retransmit = 0
                while seq_id < ack_id:
                    per_packet_delay[seq_id] = time.time() - per_packet_delay[seq_id]
                    seq_id += MESSAGE_SIZE

            if seq_id == max_seq_id:
                if WINDOW_SIZE < SSTHRESH:
                    fast_retransmit = 0
                    WINDOW_SIZE *= 2
                else:
                    fast_retransmit = 0
                    WINDOW_SIZE += 10
                max_seq_id = send_window_size(seq_id)

        except socket.timeout:
            fast_retransmit = 0
            reset_window_size()
            resend_message(seq_id)

udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.bind(("0.0.0.0", 5000))
udp_socket.settimeout(0.1)

try:
    seq_id = 0
    max_seq_id = 0
    StartThroughputTime = time.time()
    fast_retransmit = 0
    acks_num = 0
    per_packet_delay = {}

    ack_thread = threading.Thread(target=ack_receiver)
    ack_thread.start()

    max_seq_id = send_window_size(seq_id)
    while seq_id < len(data):
        if seq_id + MESSAGE_SIZE >= len(data):
            break

        if not ack_thread.is_alive():
            break

        if time.time() - StartThroughputTime > 60:
            print("Timeout reached")
            break

finally:
    stop_thread = True
    ack_thread.join()
    send_closing_message(seq_id)
    udp_socket.close()

    totalTime = time.time() - StartThroughputTime
    totalPackages = int(len(data) / MESSAGE_SIZE) + (len(data) % MESSAGE_SIZE > 0)

    print(round(len(data) / totalTime, 2).__str__() + ",")
    print(round(sum(per_packet_delay.values()) / len(per_packet_delay), 2).__str__() + ",")
    print(round((len(data) / totalTime) / (sum(per_packet_delay.values()) / len(per_packet_delay)), 2).__str__())
