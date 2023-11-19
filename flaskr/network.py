import zmq
import threading
import time

class Node:
    def __init__(self, id, port, peers):
        self.id = id
        self.port = port
        self.peers = peers
        self.context = zmq.Context()
        self.router_socket = self.context.socket(zmq.ROUTER)
        self.devices = {}

    def start(self):
        threading.Thread(target=self.start_router_socket).start()
        for peer in self.peers:
            threading.Thread(target=self.start_dealer_socket, args=(peer,)).start()

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
            day_time = time.strftime("%H:%M:%S", time.localtime())
            if message.startswith("Hello from Node"):
                peer = message.split(" ")[3]
                self.devices[peer] = day_time
            elif message.endswith("is pinging you!"):
                self.send_message_to_peer(f"{self.id} is up and running!", peer)
            else:
                self.send_message_to_peer(f"Node {self.id} says hi!", peer)

    def start_dealer_socket(self, peer):
        dealer_socket = self.context.socket(zmq.DEALER)
        print(f"Node {self.id} (You) connecting to Node {peer}")
        dealer_socket.connect(f"tcp://{peer}")
        dealer_socket.send_string(f"Hello from Node {self.id}")
        dealer_socket.close()

    def get_devices(self):
        return self.devices

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            self.send_message_to_peer(f"{self.id} is pinging you!", device)
            reply = self.router_socket.recv()
            try:
                reply = reply.decode('utf-8')
            except UnicodeDecodeError:
                return "Could not decode reply"
            return reply
        else:
            return "Device not found"

    def send_message_to_peer(self, message, peer):
        dealer_socket = self.context.socket(zmq.DEALER)
        dealer_socket.connect(f"tcp://{peer}")
        dealer_socket.send_string(message)
        dealer_socket.close()

    def join(self):
        try:
            self.router_socket.close()
        finally:
            self.context.term()
