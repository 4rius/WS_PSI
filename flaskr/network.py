import zmq
import threading
import time
import socket
import platform


class Node:
    def __init__(self, id, port, peers):
        self.id = id  # IP local
        self.port = port  # Puerto local
        self.peers = peers  # Lista de peers
        self.context = zmq.Context()  # Contexto de ZMQ
        self.router_socket = self.context.socket(zmq.ROUTER)  # Socket ROUTER
        self.devices = {}  # Dispositivos conectados

    def start(self):
        threading.Thread(target=self.start_router_socket).start()
        time.sleep(1)  # Dar tiempo para que el socket ROUTER se inicie

        # Conectar con los peers
        for peer in self.peers:
            print(f"Node {self.id} (You) connecting to Node {peer}")
            dealer_socket = self.context.socket(zmq.DEALER)
            dealer_socket.connect(f"tcp://{peer}")
            if peer not in self.devices:
                dealer_socket.send_string(f"Hello from Node {self.id}")
            peer = peer.split(":")[0]
            self.devices[peer] = {"socket": dealer_socket, "last_seen": None}
            # Con esta aproximación, si un peer se desconecta y luego se vuelve a conectar,
            # se le enviará un mensaje de bienvenida y se actualizará su timestamp
            # Cada peer tiene un socket DEALER para enviar mensajes

    def start_router_socket(self):
        # Iniciar el socket ROUTER
        self.router_socket.bind(f"tcp://*:{self.port}")
        print(f"Node {self.id} (You) listening on port {self.port}")

        while True:
            # Recibir mensajes con el identificador del dispositivo
            sender, message = self.router_socket.recv_multipart()
            try:
                message = message.decode('utf-8')
            except UnicodeDecodeError:
                continue
            print(f"Node {self.id} (You) received: {message}")
            day_time = time.strftime("%H:%M:%S", time.localtime())
            # Respuestas a los mensajes recibidos
            if message.startswith("Hello from Node"):
                # Si el dispositivo no está en la lista, agregarlo
                if sender not in self.devices:
                    self.devices[sender] = {"socket": self.context.socket(zmq.DEALER), "last_seen": day_time}
                    self.devices[sender]["socket"].connect(f"tcp://{sender}")
                # Actualizar la lista de dispositivos
                peer = message.split(" ")[3]
                self.devices[peer]["last_seen"] = day_time
                self.devices[peer]["socket"].send_string(f"Added {peer} to my network - From Node {self.id}")
            elif message.endswith("is pinging you!"):
                peer = message.split(" ")[0]
                self.devices[peer]["last_seen"] = day_time
                self.devices[peer]["socket"].send_string(f"{self.id} is up and running!")
            elif message.startswith("Added "):
                peer = message.split(" ")[1]
                self.devices[peer]["last_seen"] = day_time
            else:
                print(f"{self.id} received: {message} but doesn't know what to do with it")
                peer = message.split(" ")[0]
                self.devices[peer]["last_seen"] = day_time

    def get_devices(self):
        return {device: info["last_seen"] for device, info in self.devices.items()}

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            attempts = 0
            while attempts < 3:  # Intenta el ping 3 veces
                self.devices[device]["socket"].send_string(f"{self.id} is pinging you!")
                try:
                    reply = self.router_socket.recv(flags=zmq.NOBLOCK)
                    try:
                        reply = reply.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                    if reply == f"{device} is up and running!":
                        self.devices[device]["last_seen"] = time.strftime("%H:%M:%S", time.localtime())
                        print(f"{device} - Ping OK")
                        return device + " - Ping OK"
                except zmq.error.Again:
                    print(f"{device} - Ping FAIL - Retrying...")
                    time.sleep(1.5)  # Esperar antes de intentar de nuevo
                attempts += 1
            print(f"Device {device} - Ping FAIL - Device may have been disconnected")
            self.devices[device]["last_seen"] = False
            return device + " - Ping FAIL - Device likely disconnected"
        else:
            print("Device not found")
            return "Device not found"

    def broadcast_message(self, message):
        for device in self.devices:
            self.devices[device]["socket"].send_string(message)

    def join(self):
        for device in self.devices:
            self.devices[device]["socket"].close()
        self.router_socket.close()
        self.context.term()


def get_local_ip():
    system = platform.system()

    # macOS y Linux
    if system == "Linux" or system == "Darwin":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 80))  # No tiene ni que ser un host real
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            print("Error fetching IP, using loopback")
            return socket.gethostbyname(socket.gethostname())
    elif system == "Windows":
        return socket.gethostbyname(socket.gethostname())
