import random
import threading
import time

import zmq

from flaskr.handlers.SchemeHandler import SchemeHandler
from flaskr.helpers.DbConstants import DEFL_DOMAIN, DEFL_SET_SIZE


class Node:
    __instance = None

    @staticmethod
    def getinstance():
        """ Static access method. """
        if Node.__instance is None:
            raise Exception("Use the appropiate constructor!")
        return Node.__instance

    def __init__(self, id, port, peers):
        """ Virtually private constructor. """
        if Node.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Node.__instance = self
            self.running = True  # Saber si el nodo está corriendo por si queremos desconectarnos en algún momento
            self.id = id  # IP local
            self.port = port  # Puerto local
            self.peers = peers  # Lista de peers
            self.context = zmq.Context()  # Contexto de ZMQ
            self.router_socket = self.context.socket(zmq.ROUTER)  # Socket ROUTER
            self.devices = {}  # Dispositivos conectados
            self.myData = set(random.sample(range(DEFL_DOMAIN), DEFL_SET_SIZE))  # Conjunto de datos del nodo
            self.domain = DEFL_DOMAIN  # Dominio de los números aleatorios sobre los que se trabaja
            self.results = {}  # Resultados de las intersecciones
            self.scheme_handler = SchemeHandler(self.id, self.myData, self.domain, self.devices, self.results)
            # Manejador de esquemas criptográficos

    def start(self):
        print(f"Node {self.id} (You) starting...")
        print(f"Node {self.id} (You) - My data: {self.myData}")

        # Iniciar el socket ROUTER en un hilo
        threading.Thread(target=self.start_router_socket).start()
        time.sleep(1)  # Dar tiempo para que el socket ROUTER se inicie

        # Conectar con los peers
        self.connect_to_peers()

    def connect_to_peers(self):
        for peer in self.peers:
            print(f"Node {self.id} (You) connecting to Node {peer}")
            self._connect_to_peer(peer)

    def _connect_to_peer(self, peer):
        dealer_socket = self.context.socket(zmq.DEALER)
        dealer_socket.connect(f"tcp://{peer}")
        dealer_socket.send_string(f"DISCOVER: Node {self.id} is looking for peers")

        # Update devices dictionary
        if "[" in peer and "]" in peer:  # IPv6 address
            address = peer.split("]:")[0] + "]"
        else:  # IPv4 address
            address = peer.split(":")[0]
        self.devices[address] = {"socket": dealer_socket, "last_seen": None}

    def start_router_socket(self):
        self.router_socket.bind(f"tcp://*:{self.port}")
        print(f"Node {self.id} (You) listening on port {self.port}")
        threading.Thread(target=self._listen_on_router, daemon=True).start()
        # daemon=True para que el hilo muera cuando el programa principal muera

    def _listen_on_router(self):
        while self.running:
            sender, message = self.router_socket.recv_multipart()
            message = message.decode('utf-8')
            print(f"Node {self.id} (You) received: {message}")
            day_time = time.strftime("%H:%M:%S", time.localtime())
            self.handle_message(sender, message, day_time)

    def handle_message(self, sender, message, day_time):
        # Cleaner routing
        message_handlers = {
            "DISCOVER:": self.handle_discover,
            "DISCOVER_ACK:": self.handle_discover_ack,
            "Added ": self.handle_added
        }
        if message.endswith("is pinging you!"):
            self.handle_ping(sender, message, day_time)
        elif message.startswith("{"):
            if "implementation" in message:
                self.scheme_handler.handle_message(message)
            # Aquí podría haber otro tipo de JSON añadiendo las condiciones necesarias
        else:
            for key in message_handlers:
                if message.startswith(key):
                    message_handlers[key](message, day_time)
                    return
            self.handle_unknown(message, day_time)

    def handle_ping(self, sender, message, day_time):
        peer = message.split(" ")[0]
        if peer not in self.devices:
            self.new_peer(peer, day_time)
        self.devices[peer]["last_seen"] = day_time
        self.router_socket.send_multipart([sender, f"{self.id} is up and running!".encode('utf-8')])

    def handle_discover(self, message, day_time):
        peer = message.split(" ")[2]
        if peer not in self.devices:
            self.new_peer(peer, day_time)
        self.devices[peer]["last_seen"] = day_time
        self.devices[peer]["socket"].send_string(f"DISCOVER_ACK: Node {self.id} acknowledges node {peer}")

    def handle_discover_ack(self, message, day_time):
        peer = message.split(" ")[2]
        if peer not in self.devices:
            self.new_peer(peer, day_time)
        self.devices[peer]["last_seen"] = day_time
        self.devices[peer]["socket"].send_string(f"Added {peer} to my network - From Node {self.id}")

    def handle_added(self, message, day_time):
        peer = message.split(" ")[8]
        self.devices[peer]["last_seen"] = day_time

    def handle_unknown(self, message, day_time):
        print(f"{self.id} (You) received: {message} but don't know what to do with it")
        peer = message.split(" ")[0]
        self.devices[peer]["last_seen"] = day_time

    def get_devices(self):
        return {device: info["last_seen"] for device, info in self.devices.items()}

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            attempts = 0
            max_attempts = 3

            while attempts < max_attempts:
                self.devices[device]["socket"].send_string(f"{self.id} is pinging you!")

                try:
                    reply = self.devices[device]["socket"].recv_string(zmq.NOBLOCK)
                    print(f"{device} - Received: {reply}")

                    if reply.endswith("is up and running!"):
                        self.devices[device]["last_seen"] = time.strftime("%H:%M:%S", time.localtime())
                        print(f"{device} - Ping OK")
                        return device + " - Ping OK"
                    else:
                        print(f"{device} - Ping FAIL - Unexpected response: {reply}")
                        return device + " - Ping FAIL - Unexpected response: " + reply

                except zmq.error.Again:
                    print(f"{device} - Ping FAIL - Retrying...")
                    time.sleep(1)
                    attempts += 1

            print(f"Device {device} - Ping FAIL - Device likely disconnected")
            self.devices[device]["last_seen"] = False
            return device + " - Ping FAIL - Device likely disconnected"
        else:
            print("Device not found")
            return "Device not found"

    def broadcast_message(self, message):
        for device in self.devices:
            self.devices[device]["socket"].send_string(message)

    def stop(self):
        # Cierra todos los sockets de los dispositivos
        for device in self.devices.values():
            device["socket"].close()
        # Cierra el socket ROUTER
        self.router_socket.close()
        # Cierra el executor
        self.scheme_handler.executor.shutdown(wait=True)
        # Cambia el estado de ejecución a False
        self.running = False

    def genkeys(self, scheme):
        if scheme == "Paillier":
            t = threading.Thread(target=self.scheme_handler.genkeys, args=("Paillier",))
            t.start()
            return "Generating Paillier keys..."
        elif scheme == "Damgard-Jurik":
            t = threading.Thread(target=self.scheme_handler.genkeys, args=("Damgard-Jurik",))
            t.start()
            return "Generating Damgard-Jurik keys..."
        return "Invalid scheme"

    def new_peer(self, peer, last_seen):
        dealer_socket = self.context.socket(zmq.DEALER)
        dealer_socket.connect(f"tcp://{peer}:{self.port}")
        self.devices[peer] = {"socket": dealer_socket, "last_seen": last_seen}
        print(f"Added {peer} to my network")

    def discover_peers(self):
        print(f"Node {self.id} (You) - Discovering peers on port {self.port}")
        # Iterar sobre todas las direcciones IP posibles en la subred
        for i in range(1, 256):
            ip = f"192.168.1.{i}"
            if ip not in self.devices and ip != self.id:
                try:
                    # Crear un nuevo socket y tratar de conectar
                    dealer_socket = self.context.socket(zmq.DEALER)
                    print(f"Node {self.id} (You) - Trying to connect to " + ip)
                    dealer_socket.setsockopt(zmq.RCVTIMEO, 1000)  # Tiempo de espera de 1 segundo
                    dealer_socket.connect(f"tcp://{ip}:{self.port}")
                    # Enviar un mensaje de descubrimiento
                    dealer_socket.send_string(f"DISCOVER: Node {self.id} is looking for peers")
                    # Matamos aquí el socket para no tener que esperar a que expire el tiempo de espera
                    dealer_socket.close()
                except zmq.error.Again:
                    continue
        return "Discovering peers..."

    def start_intersection(self, device, scheme, type=None):
        if device in self.devices:
            return self.scheme_handler.start_intersection(device, scheme, type)
        return "Device not found - Have the peer send an ACK first"

    def launch_test(self, device):
        if device in self.devices:
            self.scheme_handler.test_launcher(device)
            return "Launching a massive test with " + device + " - Check logs"
        return "Device not found"
