import json
import random
import threading
import time

import zmq

from flaskr import Logs
from flaskr.JSONExtractor import extract_peer_data
from flaskr.implementations.Damgard_jurik import encrypt_my_data_dj, serialize_public_key_dj, get_encrypted_set_dj, \
    get_multiplied_set_dj, recv_multiplied_set_dj, generate_keypair_dj
from flaskr.implementations.Paillier import generate_paillier_keys, serialize_public_key, \
    get_encrypted_set, get_multiplied_set, recv_multiplied_set, encrypt_my_data


class Node:
    def __init__(self, id, port, peers):
        self.running = True  # Saber si el nodo está corriendo por si queremos desconectarnos en algún momento
        self.id = id  # IP local
        self.port = port  # Puerto local
        self.peers = peers  # Lista de peers
        self.context = zmq.Context()  # Contexto de ZMQ
        self.router_socket = self.context.socket(zmq.ROUTER)  # Socket ROUTER
        self.devices = {}  # Dispositivos conectados
        self.privkey_paillier = None  # Clave privada del nodo
        self.pubkey_paillier = None  # Clave pública del nodo
        self.privkeyring_dj = None
        self.pubkey_dj = None
        self.myData = set(random.sample(range(40), 10))  # Conjunto de datos del nodo (set de 10 números aleatorios)
        self.domain = 40  # Dominio de los números aleatorios sobre los que se trabaja
        self.results = {}  # Resultados de las intersecciones

    def start(self):
        print(f"Node {self.id} (You) starting...")
        # Por defecto se generan las claves del nodo usando la implementación de Paillier de phe
        self.privkey_paillier, self.pubkey_paillier = generate_paillier_keys()
        self.pubkey_dj, self.privkeyring_dj = generate_keypair_dj()
        print(
            f"Node {self.id} (You) - Paillier keys generated - Objects: {self.privkey_paillier} - {self.pubkey_paillier}")
        print(
            f"Node {self.id} (You) - Damgard-Jurik keys generated - Objects: {self.pubkey_dj} - {self.privkeyring_dj}")
        print(f"Node {self.id} (You) - My data: {self.myData}")

        # Iniciar el socket ROUTER en un hilo
        threading.Thread(target=self.start_router_socket).start()
        time.sleep(1)  # Dar tiempo para que el socket ROUTER se inicie

        # Conectar con los peers
        for peer in self.peers:
            print(f"Node {self.id} (You) connecting to Node {peer}")
            dealer_socket = self.context.socket(zmq.DEALER)
            dealer_socket.connect(f"tcp://{peer}")
            if peer not in self.devices:
                dealer_socket.send_string(f"DISCOVER: Node {self.id} is looking for peers")
            if "[" in peer and "]" in peer:  # Si es una dirección IPv6
                peer = peer.split("]:")[0] + "]"
            else:  # Si es una dirección IPv4
                peer = peer.split(":")[0]
            self.devices[peer] = {"socket": dealer_socket, "last_seen": None}
            # Con esta aproximación, si un peer se desconecta y luego se vuelve a conectar,
            # se le enviará un mensaje de bienvenida y se actualizará su timestamp
            # Cada peer tiene un socket DEALER para enviar mensajes

    def start_router_socket(self):
        # Iniciar el socket ROUTER
        self.router_socket.bind(f"tcp://*:{self.port}")
        print(f"Node {self.id} (You) listening on port {self.port}")

        while self.running:
            # Recibir mensajes con el identificador del dispositivo
            sender, message = self.router_socket.recv_multipart()
            try:
                message = message.decode('utf-8')
            except UnicodeDecodeError:
                continue
            print(f"Node {self.id} (You) received: {message}")
            day_time = time.strftime("%H:%M:%S", time.localtime())
            # Respuestas a los mensajes recibidos
            self.handle_message(sender, message, day_time)
        self.router_socket.close()
        self.router_socket.unbind(f"tcp://*:{self.port}")
        self.context.term()

    def handle_message(self, sender, message, day_time):
        if message.endswith("is pinging you!"):
            self.handle_ping(sender, message, day_time)
        elif message.startswith("DISCOVER:"):
            self.handle_discover(message, day_time)
        elif message.startswith("DISCOVER_ACK:"):
            self.handle_discover_ack(message, day_time)
        elif message.startswith("Added "):
            self.handle_added(message, day_time)
        elif message.startswith("{"):
            self.intersection_second_step(message)
        elif "implementation" in message and "peer" in message:
            self.handle_intersection(message)
        else:
            self.handle_unknown(message, day_time)

    def handle_ping(self, sender, message, day_time):
        peer = message.split(" ")[0]
        self.devices[peer]["last_seen"] = day_time
        self.router_socket.send_multipart([sender, f"{self.id} is up and running!".encode('utf-8')])

    def handle_discover(self, message, day_time):
        peer = message.split(" ")[2]
        if peer not in self.devices:
            self.new_peer(peer, day_time)
        self.devices[peer]["socket"].send_string(f"DISCOVER_ACK: Node {self.id} acknowledges node {peer}")

    def handle_discover_ack(self, message, day_time):
        peer = message.split(" ")[2]
        if peer not in self.devices:
            self.new_peer(peer, day_time)
        self.devices[peer]["socket"].send_string(f"Added {peer} to my network - From Node {self.id}")

    def handle_added(self, message, day_time):
        peer = message.split(" ")[8]
        self.devices[peer]["last_seen"] = day_time

    def handle_intersection(self, message):
        try:
            peer_data = json.loads(message)
            crypto_scheme = peer_data.pop('cryptpscheme')
            if crypto_scheme == "Paillier":
                self.paillier_intersection_final_step(peer_data)
            elif crypto_scheme == "Damgard-Jurik":
                self.damgard_jurik_intersection_final_step(peer_data)
        except json.JSONDecodeError:
            print("Received message is not a valid JSON.")

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

    def join(self):
        self.running = False
        for device in self.devices:
            self.devices[device]["socket"].close()
        self.devices = {}

    def gen_paillier(self):
        start_time = time.time()
        Logs.start_logging()
        self.privkey_paillier, self.pubkey_paillier = generate_paillier_keys()
        end_time = time.time()
        Logs.stop_logging_cpu_usage()
        Logs.stop_logging_ram_usage()
        Logs.log_activity("GENKEYS_PAILLIER", end_time - start_time, "1.0 - DEV - WS", self.id)
        return "New Paillier keys generated"

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

    def intersection_second_step(self, message):
        start_time = time.time()
        Logs.start_logging()
        peer_data = extract_peer_data(message)
        implementation = peer_data['implementation']

        if implementation == "Paillier":
            encrypted_set = get_encrypted_set(peer_data['data'], peer_data['pubkey'])
            self.handle_paillier(peer_data, encrypted_set)
        elif implementation == "Damgard-Jurik":
            encrypted_set = get_encrypted_set_dj(peer_data['data'], peer_data['pubkey'])
            self.handle_damgard_jurik(peer_data, encrypted_set)

        end_time = time.time()
        Logs.stop_logging_cpu_usage()
        Logs.stop_logging_ram_usage()
        Logs.log_activity("INTERSECTION_" + implementation + "_2", end_time - start_time, "1.0 - DEV - WS", self.id,
                          peer_data['peer'])

    def handle_paillier(self, peer_data, encrypted_set):
        multiplied_set = get_multiplied_set(encrypted_set, self.myData)
        self.send_message(peer_data, multiplied_set, 'Paillier')

    def handle_damgard_jurik(self, peer_data, encrypted_set):
        multiplied_set = get_multiplied_set_dj(encrypted_set, self.myData)
        self.send_message(peer_data, multiplied_set, 'Damgard-Jurik')

    def send_message(self, peer_data, multiplied_set, cryptpscheme):
        serialized_multiplied_set = {element: str(encrypted_value.ciphertext()) for
                                     element, encrypted_value in multiplied_set.items()}
        message = {'data': serialized_multiplied_set, 'peer': self.id, 'cryptpscheme': cryptpscheme}
        self.devices[peer_data['peer']]["socket"].send_json(message)

    def intersection_final_step(self, peer_data, decrypt_function, implementation):
        multiplied_set = {}
        start_time = time.time()
        Logs.start_logging()
        if implementation == "Paillier":
            multiplied_set = recv_multiplied_set(peer_data['data'], self.pubkey_paillier)
        elif implementation == "Damgard-Jurik":
            multiplied_set = recv_multiplied_set_dj(peer_data['data'], self.pubkey_dj)
        device = peer_data['peer']
        for element, encrypted_value in multiplied_set.items():
            multiplied_set[element] = decrypt_function(encrypted_value)
        multiplied_set = {element for element, value in multiplied_set.items() if value == 1}
        self.results[device] = multiplied_set
        end_time = time.time()
        Logs.stop_logging_cpu_usage()
        Logs.stop_logging_ram_usage()
        Logs.log_activity("INTERSECTION_" + implementation + "_F", end_time - start_time, "1.0 - DEV - WS", self.id,
                          device)
        print(f"Intersection with {device} - {implementation} - Result: {multiplied_set}")

    def paillier_intersection_final_step(self, peer_data):
        self.intersection_final_step(peer_data, self.pubkey_paillier.decrypt, 'Paillier')

    def damgard_jurik_intersection_final_step(self, peer_data):
        self.intersection_final_step(peer_data, self.pubkey_paillier.decrypt, 'Damgard-Jurik')

    def intersection_first_step(self, device, encrypt_function, serialize_function, pubkey, implementation):
        if device in self.devices:
            start_time = time.time()
            Logs.start_logging()
            encrypted_data = encrypt_function(self.myData, pubkey, self.domain)
            serialized_pubkey = serialize_function(pubkey)
            if implementation == "Paillier":
                for element, encrypted_value in encrypted_data.items():
                    encrypted_data[element] = str(encrypted_value.ciphertext())
            elif implementation == "Damgard-Jurik":
                for element, encrypted_value in encrypted_data.items():
                    encrypted_data[element] = str(encrypted_value.value)
            print(f"Intersection with {device} - {implementation} - Sending data: {encrypted_data}")
            message = {'data': encrypted_data, 'implementation': implementation, 'peer': self.id,
                       'pubkey': serialized_pubkey}
            self.devices[device]["socket"].send_json(message)
            end_time = time.time()
            Logs.stop_logging_cpu_usage()
            Logs.stop_logging_ram_usage()
            Logs.log_activity("INTERSECTION_" + implementation + "_1", end_time - start_time, "1.0 - DEV - WS", self.id,
                              device)
            return "Intersection with " + device + " - " + implementation + " - Waiting for response..."
        else:
            return "Device not found"

    def dj_intersection_first_step(self, device):
        self.intersection_first_step(device, encrypt_my_data_dj, serialize_public_key_dj, self.pubkey_dj,
                                     'Damgard-Jurik')

    def paillier_intersection_first_step(self, device):
        self.intersection_first_step(device, encrypt_my_data, serialize_public_key, self.pubkey_paillier,
                                     'Paillier')
