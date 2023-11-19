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
        self.rep_socket = self.context.socket(zmq.REP)
        self.req_socket = self.context.socket(zmq.REQ)
        self.devices = {}

    def start(self):
        # Que se ejecuten en hilos separados porque son loops infinitos y podrían bloquear el programa
        threading.Thread(target=self.start_rep_socket).start()
        threading.Thread(target=self.start_req_socket).start()

    def start_rep_socket(self):
        self.rep_socket.bind(f"tcp://*:{self.port}")
        print(f"Node {self.id} listening on port {self.port}")
        time.sleep(1)  # Esperar un segundo para que el socket se inicialice
        while True:
            if self.rep_socket.poll(timeout=1000):  # Ver si hay mensajes
                message = self.rep_socket.recv_string()
                print(f"Node {self.id} received: {message}")
                self.devices[message] = time.time()
                self.rep_socket.send_string(f"Node {self.id} says hi!")

    def start_req_socket(self):
        for peer in self.peers:
            print(f"Node {self.id} connecting to Node {peer}")
            self.req_socket.connect(f"tcp://localhost:{peer}")
            self.req_socket.send_string(f"Hello from Node {self.id}")
            print(f"Node {self.id} received reply: {self.req_socket.recv_string()}")

    def get_devices(self):
        return self.devices

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            self.req_socket.send_string(f"Ping from Node {self.id}")
            print(f"Node {self.id} received reply: {self.req_socket.recv_string()}")
        else:
            print(f"Device {device} not found.")

    def join(self):
        self.rep_socket.close()
        self.req_socket.close()
        self.context.term()


# Obtener la dirección IP local
local_ip = socket.gethostbyname(socket.gethostname())

# Crear nodos con default values para poder llamarlo sin argumentos
node = Node(local_ip, 5001, [])

# Iniciar nodos
node.start()

# Esperar a que los nodos terminen
node.join()
