import zmq
import threading
import time

class Node:
    def __init__(self, id, port, peers):
        self.id = id
        self.port = port
        self.peers = peers
        self.context = zmq.Context()
        self.pub_socket = self.context.socket(zmq.PUB)
        self.sub_sockets = {}

    def start(self):
        threading.Thread(target=self.start_pub_socket).start()
        for peer in self.peers:
            threading.Thread(target=self.start_sub_socket, args=(peer,)).start()

    def start_pub_socket(self):
        self.pub_socket.bind(f"tcp://*:{self.port}")
        print(f"Node {self.id} (You) listening on port {self.port}")
        time.sleep(1)

    def start_sub_socket(self, peer):
        sub_socket = self.context.socket(zmq.SUB)
        sub_socket.connect(f"tcp://{peer}")
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.sub_sockets[peer] = sub_socket
        while True:
            message = sub_socket.recv_string()
            print(f"Node {self.id} (You) received: {message}")

    def send_message(self, message):
        self.pub_socket.send_string(message)

    def ping_device(self, device):
        if device in self.sub_sockets:
            print(f"Pinging device: {device}")
            self.send_message(f"{self.id} is pinging you!")
        else:
            print("Device not found")

    def join(self):
        for sub_socket in self.sub_sockets.values():
            sub_socket.close()
        self.pub_socket.close()
        self.context.term()
