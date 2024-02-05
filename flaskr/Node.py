import json
import random
import threading
import time

import psutil
import zmq

from flaskr import Logs
from flaskr.implementations.Damgard_jurik import encrypt_my_data_dj, serialize_public_key_dj, reconstruct_public_key_dj, \
    get_encrypted_set_dj, get_multiplied_set_dj, recv_multiplied_set_dj
from flaskr.implementations.Paillier import generate_paillier_keys, serialize_public_key, \
    reconstruct_public_key, get_encrypted_set, get_multiplied_set, recv_multiplied_set, encrypt_my_data


class Node:
    def __init__(self, id, port, peers):
        self.running = True  # Saber si el nodo está corriendo por si queremos desconectarnos en algún momento
        self.id = id  # IP local
        self.port = port  # Puerto local
        self.peers = peers  # Lista de peers
        self.context = zmq.Context()  # Contexto de ZMQ
        self.router_socket = self.context.socket(zmq.ROUTER)  # Socket ROUTER
        self.devices = {}  # Dispositivos conectados
        self.pkey = None  # Clave privada del nodo
        self.skey = None  # Clave pública del nodo
        self.myData = set(random.sample(range(40), 10))  # Conjunto de datos del nodo (set de 10 números aleatorios)
        self.domain = 40  # Dominio de los números aleatorios sobre los que se trabaja
        self.results = {}  # Resultados de las intersecciones

    def start(self):
        print(f"Node {self.id} (You) starting...")
        # Por defecto se generan las claves del nodo usando la implementación de Paillier de phe
        self.pkey, self.skey = generate_paillier_keys()
        print(f"Node {self.id} (You) - Keys generated - Objects: {self.pkey} - {self.skey}")
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
            peer = message.split(" ")[0]
            self.devices[peer]["last_seen"] = day_time
            # Se manda con el router_socket para que lo pueda consumir ping_devices y no lo consuma el router del
            # peer
            self.router_socket.send_multipart([sender, f"{self.id} is up and running!".encode('utf-8')])
        elif message.startswith("DISCOVER:"):
            peer = message.split(" ")[2]
            if peer not in self.devices:
                self.new_peer(peer, day_time)
            self.devices[peer]["socket"].send_string(f"DISCOVER_ACK: Node {self.id} acknowledges node {peer}")
        elif message.startswith("DISCOVER_ACK:"):
            peer = message.split(" ")[2]
            if peer not in self.devices:
                self.new_peer(peer, day_time)
            self.devices[peer]["socket"].send_string(f"Added {peer} to my network - From Node {self.id}")
        elif message.startswith("Added "):
            peer = message.split(" ")[8]
            self.devices[peer]["last_seen"] = day_time
        # Si recibe un json, es que el peer quiere calcular la intersección
        elif "implementation" in message and "peer" in message:
            self.paillier_intersection_second_step(message)
        # Resto del cálculo de la intersección
        elif message.startswith("{"):
            try:
                peer_data = json.loads(message)
                crypto_scheme = peer_data.pop('cryptpscheme')
                if crypto_scheme == "Paillier":
                    self.paillier_intersection_final_step(peer_data)
            except json.JSONDecodeError:
                print("Received message is not a valid JSON.")
        else:
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
        self.pkey, self.skey = generate_paillier_keys()
        end_time = time.time()
        Logs.stop_logging_cpu_usage()
        Logs.stop_logging_ram_usage()
        Logs.log_activity("GENKEYS_PAILLIER", end_time - start_time , "1.0 - DEV - WS", self.id)
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

    def paillier_intersection_first_step(self, device):
        # Se cifra el conjunto de datos del nodo y se envía al peer
        if device in self.devices:
            print(f"Node {self.id} (You) - Intersection with {device} - Paillier")
            start_time = time.time()
            Logs.start_logging()
            # Cifrar los datos del nodo
            encrypted_data = encrypt_my_data(self.myData, self.pkey, self.domain)
            # Enviar los datos cifrados al peer y añadimos el esquema, el peer y nuestra clave pública
            serialized_pubkey = serialize_public_key(self.pkey)
            # Poner encrypted data de forma que sea serializable
            for element, encrypted_value in encrypted_data.items():
                encrypted_data[element] = str(encrypted_value.ciphertext())
            message = {'data': encrypted_data, 'implementation': 'Paillier', 'peer': self.id,
                       'pubkey': serialized_pubkey}
            self.devices[device]["socket"].send_json(message)
            end_time = time.time()
            Logs.stop_logging_cpu_usage()
            Logs.stop_logging_ram_usage()
            Logs.log_activity("INTERSECTION_PAILLIER_1", end_time - start_time, "1.0 - DEV - WS", self.id, device)
            return "Intersection with " + device + " - Paillier - Waiting for response..."
        else:
            print("Device not found")
            return "Device not found"

    def paillier_intersection_second_step(self, message):  # Calculate intersection
        try:
            start_time = time.time()
            Logs.start_logging()
            # Intentamos deserializar el mensaje para ver si es un JSON válido
            peer_data = json.loads(message)
            # Si es un JSON válido
            peer = peer_data.pop('peer')
            implementation = peer_data.pop('implementation')
            peer_pubkey = peer_data.pop('pubkey')
            peer_pubkey_reconstructed = reconstruct_public_key(peer_pubkey)
            encrypted_set = get_encrypted_set(peer_data.pop('data'), peer_pubkey_reconstructed)
            print(f"Node {self.id} (You) - Calculating intersection with {peer} - {implementation}")
            # Generamos una lista con exponentes y valores cifrados de nuestro conjunto de datos
            # Si el esquema es Paillier, llamamos al método de intersección con los datos del peer
            if implementation == "Paillier":
                multiplied_set = get_multiplied_set(encrypted_set, self.myData)
                # Serializamos y mandamos de vuelta el resultado
                serialized_multiplied_set = {element: str(encrypted_value.ciphertext()) for
                                             element, encrypted_value in multiplied_set.items()}
                print(f"Node {self.id} (You) - Intersection with {peer} - Multiplied set: {multiplied_set}")
                message = {'data': serialized_multiplied_set, 'peer': self.id, 'cryptpscheme': implementation}
                self.devices[peer]["socket"].send_json(message)
                end_time = time.time()
                Logs.stop_logging_cpu_usage()
                Logs.stop_logging_ram_usage()
                Logs.log_activity("INTERSECTION_PAILLIER_2", end_time - start_time, "1.0 - DEV - WS", self.id, peer)
            # Aquí irán las demás implementaciones
        except json.JSONDecodeError:
            # Si hay un error al deserializar, el mensaje no es un JSON válido
            print("Received message is not a valid JSON.")
        # Rezamos

    def paillier_intersection_final_step(self, peer_data):
        start_time = time.time()
        Logs.start_logging()
        multiplied_set = peer_data.pop('data')
        multiplied_set = recv_multiplied_set(multiplied_set, self.pkey)
        device = peer_data.pop('peer')
        # Desciframos los datos del peer
        for element, encrypted_value in multiplied_set.items():
            multiplied_set[element] = self.skey.decrypt(encrypted_value)
        # Cogemos solo los valores que sean 1, que representan la intersección
        multiplied_set = {element for element, value in multiplied_set.items() if value == 1}
        # Guardamos el resultado
        self.results[device] = multiplied_set
        end_time = time.time()
        Logs.stop_logging_cpu_usage()
        Logs.stop_logging_ram_usage()
        Logs.log_activity("INTERSECTION_PAILLIER_F", end_time - start_time, "1.0 - DEV - WS", self.id, device)
        print(f"Node {self.id} (You) - Intersection with {device} - Result: {multiplied_set}")

    def damgard_jurik_intersection_first_step(self, device):
        if device in self.devices:
            print(f"Node {self.id} (You) - Intersection with {device} - Damgard-Jurik")
            start_time = time.time()
            Logs.start_logging()
            encrypted_data = encrypt_my_data_dj(self.myData, self.pkey, self.domain)
            serialized_pubkey = serialize_public_key_dj(self.pkey)
            for element, encrypted_value in encrypted_data.items():
                encrypted_data[element] = str(encrypted_value.ciphertext())
            message = {'data': encrypted_data, 'implementation': 'Damgard-Jurik', 'peer': self.id,
                       'pubkey': serialized_pubkey}
            self.devices[device]["socket"].send_json(message)
            end_time = time.time()
            Logs.stop_logging_cpu_usage()
            Logs.stop_logging_ram_usage()
            Logs.log_activity("INTERSECTION_DJ_1", end_time - start_time, "1.0 - DEV - WS", self.id, device)
            return "Intersection with " + device + " - Damgard-Jurik - Waiting for response..."
        else:
            print("Device not found")
            return "Device not found"

    def damgard_jurik_intersection_second_step(self, message):
        try:
            start_time = time.time()
            Logs.start_logging()
            peer_data = json.loads(message)
            peer = peer_data.pop('peer')
            implementation = peer_data.pop('implementation')
            peer_pubkey = peer_data.pop('pubkey')
            peer_pubkey_reconstructed = reconstruct_public_key_dj(peer_pubkey)
            encrypted_set = get_encrypted_set_dj(peer_data.pop('data'), peer_pubkey_reconstructed)
            print(f"Node {self.id} (You) - Calculating intersection with {peer} - {implementation}")
            if implementation == "Damgard-Jurik":
                multiplied_set = get_multiplied_set_dj(encrypted_set, self.myData)
                serialized_multiplied_set = {element: str(encrypted_value.ciphertext()) for
                                             element, encrypted_value in multiplied_set.items()}
                print(f"Node {self.id} (You) - Intersection with {peer} - Multiplied set: {multiplied_set}")
                message = {'data': serialized_multiplied_set, 'peer': self.id, 'cryptpscheme': implementation}
                self.devices[peer]["socket"].send_json(message)
                end_time = time.time()
                Logs.stop_logging_cpu_usage()
                Logs.stop_logging_ram_usage()
                Logs.log_activity("INTERSECTION_DJ_2", end_time - start_time, "1.0 - DEV - WS", self.id, peer)
        except json.JSONDecodeError:
            print("Received message is not a valid JSON.")

    def damgard_jurik_intersection_final_step(self, peer_data):
        start_time = time.time()
        Logs.start_logging()
        multiplied_set = peer_data.pop('data')
        multiplied_set = recv_multiplied_set_dj(multiplied_set, self.pkey)
        device = peer_data.pop('peer')
        for element, encrypted_value in multiplied_set.items():
            multiplied_set[element] = self.skey.decrypt(encrypted_value)
        multiplied_set = {element for element, value in multiplied_set.items() if value == 1}
        self.results[device] = multiplied_set
        end_time = time.time()
        Logs.stop_logging_cpu_usage()
        Logs.stop_logging_ram_usage()
        Logs.log_activity("INTERSECTION_DJ_F", end_time - start_time, "1.0 - DEV - WS", self.id, device)
        print(f"Node {self.id} (You) - Intersection with {device} - Result: {multiplied_set}")
