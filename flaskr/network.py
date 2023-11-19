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
            day_time = time.strftime("%H:%M:%S", time.localtime())
            if message.startswith("Hello from Node"):
                peer = message.split(" ")[3]
                self.devices[peer] = day_time
                self.dealer_socket.send_string(f"Hello from Node {self.id}")
            elif message.endswith("is pinging you!"):
                self.dealer_socket.send_string(f"{self.id} is up and running!")
            else:
                self.dealer_socket.send_string(f"Node {self.id} says hi!")

    def start_dealer_socket(self):
        for peer in self.peers:
            print(f"Node {self.id} (You) connecting to Node {peer}")
            self.dealer_socket.connect(f"tcp://{peer}")
            if peer not in self.devices:
                self.dealer_socket.send_string(f"Hello from Node {self.id}")

    def get_devices(self):
        return self.devices

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            self.dealer_socket.send_string(f"{self.id} is pinging you!")
            reply = self.router_socket.recv()
            try:
                reply = reply.decode('utf-8')
            except UnicodeDecodeError:
                return "Could not decode reply"
            return reply
        else:
            return "Device not found"

    def join(self):
        try:
            self.router_socket.close()
            self.dealer_socket.close()
        finally:
            self.context.term()
