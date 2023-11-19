import zmq
import threading
import time
import socket


class Node:
    def __init__(self, id, port, peers):
        self.id = id
        self.port = port
        self.peers = peers
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.dealer_socket = self.context.socket(zmq.DEALER)
        self.devices = {}

    def start(self):
        threading.Thread(target=self.start_router_socket).start()
        threading.Thread(target=self.start_dealer_socket).start()

    def start_router_socket(self):
        self.router_socket.bind(f"tcp://*:{self.port}")
        print(f"Node {self.id} (You) listening on port {self.port}")
        time.sleep(1)

        while True:
            message = self.router_socket.recv()
            try:
                message = message.decode('utf-8')
            except UnicodeDecodeError:
                continue
            print(f"Node {self.id} (You) received: {message}")
            self.devices[message] = time.time()
            self.router_socket.send_string(f"Node {self.id} says hi!")

    def start_dealer_socket(self):
        for peer in self.peers:
            print(f"Node {self.id} (You) connecting to Node {peer}")
            self.dealer_socket.connect(f"tcp://{peer}")
            self.dealer_socket.send_string(f"Hello from Node {self.id}")
            print(f"Node {self.id} (You) received reply: {self.dealer_socket.recv_string()}")

    def get_devices(self):
        return self.devices

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            self.dealer_socket.send_string(f"Ping from Node {self.id}")
            return self.dealer_socket.recv_string()
        else:
            return "Device not found"

    def join(self):
        self.router_socket.close()
        self.dealer_socket.close()
        self.context.term()
