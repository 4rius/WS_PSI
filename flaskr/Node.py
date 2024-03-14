import json
import random
import threading
import time

import zmq

from flaskr import Logs
from flaskr.DbConstants import DEFL_DOMAIN, DEFL_SET_SIZE, VERSION
from flaskr.Logs import ThreadData
from flaskr.handlers.SchemeHandler import SchemeHandler


class Node:
    def __init__(self, id, port, peers):
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
        self.scheme_handler = SchemeHandler(self.myData, self.devices, self.results, self.id, self.domain)

    def start(self):
        print(f"Node {self.id} (You) starting...")
        print(
            f"Node {self.id} (You) - Paillier keys generated - Objects: {self.scheme_handler.paillier.private_key} - {self.scheme_handler.paillier.public_key}")
        print(
            f"Node {self.id} (You) - Damgard-Jurik keys generated - Objects: {self.scheme_handler.damgard_jurik.private_key_ring} - {self.scheme_handler.damgard_jurik.public_key}")
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
            self.devices[peer] = {"socket": dealer_socket,
                                  "last_seen": None}  # Con esta aproximación, si un peer se desconecta y luego se vuelve a conectar,  # se le enviará un mensaje de bienvenida y se actualizará su timestamp  # Cada peer tiene un socket DEALER para enviar mensajes

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
        elif "cryptpscheme" in message and "peer" in message:
            self.handle_intersection(message)
        elif message.startswith("{"):
            t = threading.Thread(target=self.intersection_second_step, args=(message,))
            t.start()
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

    def handle_intersection(self, message):
        try:
            peer_data = json.loads(message)
            crypto_scheme = peer_data.pop('cryptpscheme')
            if crypto_scheme == "Paillier":
                t = threading.Thread(target=self.scheme_handler.intersection_final_step,
                                     args=(peer_data, self.scheme_handler.paillier))
                t.start()
            elif crypto_scheme == "Damgard-Jurik" or crypto_scheme == "DamgardJurik":
                t = threading.Thread(target=self.scheme_handler.intersection_final_step,
                                     args=(peer_data, self.scheme_handler.damgard_jurik))
                t.start()
            elif crypto_scheme == "Paillier_OPE" or crypto_scheme == "Paillier OPE":
                t = threading.Thread(target=self.scheme_handler.intersection_final_step_ope,
                                     args=(peer_data, self.scheme_handler.paillier))
                t.start()
            elif crypto_scheme == "Damgard-Jurik_OPE" or crypto_scheme == "DamgardJurik OPE":
                t = threading.Thread(target=self.scheme_handler.intersection_final_step_ope,
                                     args=(peer_data, self.scheme_handler.damgard_jurik))
                t.start()
            elif crypto_scheme == "Paillier PSI-CA OPE":
                t = threading.Thread(target=self.scheme_handler.final_step_psi_ca_ope,
                                     args=(peer_data, self.scheme_handler.paillier))
                t.start()
            elif crypto_scheme == "Damgard-Jurik PSI-CA OPE" or crypto_scheme == "DamgardJurik PSI-CA OPE":
                t = threading.Thread(target=self.scheme_handler.final_step_psi_ca_ope,
                                     args=(peer_data, self.scheme_handler.damgard_jurik))
                t.start()
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
        t = threading.Thread(target=self.scheme_handler.genkeys, args=("Paillier",))
        t.start()
        return "Generating Paillier keys..."

    def gen_dj(self):
        t = threading.Thread(target=self.scheme_handler.genkeys, args=("Damgard-Jurik",))
        t.start()
        return "Generating Damgard-Jurik keys..."

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
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        try:
            peer_data = json.loads(message)
        except json.JSONDecodeError:
            print("Received message is not a valid JSON.")
            return "Received message is not a valid JSON."

        implementation = peer_data['implementation']

        if implementation == "Paillier":
            peer_data, encrypted_set, cryptscheme = self.scheme_handler.handle_intersection(peer_data,
                                                                                            self.scheme_handler.paillier,
                                                                                            peer_data['pubkey'])
            self.send_message(peer_data, encrypted_set, cryptscheme)
        elif implementation == "Damgard-Jurik" or implementation == "DamgardJurik":
            peer_data, encrypted_set, cryptscheme = self.scheme_handler.handle_intersection(peer_data,
                                                                                            self.scheme_handler.damgard_jurik,
                                                                                            peer_data['pubkey'])
            self.send_message(peer_data, encrypted_set, cryptscheme)
        elif implementation == "Paillier_OPE" or implementation == "Paillier OPE":
            peer_data, encrypted_evaluated_coeffs, cryptscheme = self.scheme_handler.handle_ope(peer_data,
                                                                                                peer_data['data'],
                                                                                                peer_data['pubkey'],
                                                                                                self.scheme_handler.paillier)
            self.send_message(peer_data, encrypted_evaluated_coeffs, cryptscheme)
        elif implementation == "Damgard-Jurik_OPE" or implementation == "DamgardJurik OPE":
            peer_data, encrypted_evaluated_coeffs, cryptscheme = self.scheme_handler.handle_ope(peer_data,
                                                                                                peer_data['data'],
                                                                                                peer_data['pubkey'],
                                                                                                self.scheme_handler.damgard_jurik)
            self.send_message(peer_data, encrypted_evaluated_coeffs, cryptscheme)

        elif implementation == "Paillier PSI-CA OPE":
            evaluations = self.scheme_handler.handle_psi_ca_ope(peer_data['data'], peer_data['pubkey'],
                                                                self.scheme_handler.paillier)
            self.send_message(peer_data, evaluations, "Paillier PSI-CA OPE")

        elif implementation == "Damgard-Jurik PSI-CA OPE" or implementation == "DamgardJurik PSI-CA OPE":
            evaluations = self.scheme_handler.handle_psi_ca_ope(peer_data['data'], peer_data['pubkey'],
                                                                self.scheme_handler.damgard_jurik)
            self.send_message(peer_data, evaluations, "Damgard-Jurik PSI-CA OPE")

        end_time = time.time()
        Logs.stop_logging(thread_data)
        if implementation.endswith("PSI-CA OPE"):
            Logs.log_activity(thread_data, "CARDINALITY_" + implementation + "_2", end_time - start_time, VERSION,
                              self.id, peer_data['peer'])
        else:
            Logs.log_activity(thread_data, "INTERSECTION_" + implementation + "_2", end_time - start_time, VERSION,
                              self.id, peer_data['peer'])

    def send_message(self, peer_data, set, cryptpscheme):
        set_to_send = {}
        if cryptpscheme == "Paillier":
            set_to_send = {element: str(encrypted_value.ciphertext()) for element, encrypted_value in set.items()}
        elif cryptpscheme == "Damgard-Jurik" or cryptpscheme == "DamgardJurik":
            set_to_send = {element: str(encrypted_value.value) for element, encrypted_value in set.items()}
        elif cryptpscheme == "Paillier_OPE" or cryptpscheme == "Paillier OPE" or cryptpscheme == "Paillier PSI-CA OPE":
            set_to_send = [str(encrypted_value.ciphertext()) for encrypted_value in set]
        elif cryptpscheme == "Damgard-Jurik_OPE" or cryptpscheme == "DamgardJurik OPE" or cryptpscheme == "Damgard-Jurik PSI-CA OPE":
            set_to_send = [str(encrypted_value.value) for encrypted_value in set]
        message = {'data': set_to_send, 'peer': self.id, 'cryptpscheme': cryptpscheme}
        self.devices[peer_data['peer']]["socket"].send_json(message)

    def dj_intersection_first_step(self, device):
        if device in self.devices:
            t = threading.Thread(target=self.scheme_handler.intersection_first_step,
                                 args=(device, self.scheme_handler.damgard_jurik))
            t.start()
            return "Intersection with " + device + " - Damgard-Jurik - Thread started, check logs"
        return "Device not found"

    def paillier_intersection_first_step(self, device):
        if device in self.devices:
            t = threading.Thread(target=self.scheme_handler.intersection_first_step,
                                 args=(device, self.scheme_handler.paillier))
            t.start()
            return "Intersection with " + device + " - Paillier - Thread started, check logs"
        return "Device not found"

    def paillier_intersection_first_step_ope(self, device, type="PSI"):
        if device in self.devices:
            t = threading.Thread(target=self.scheme_handler.intersection_first_step_ope,
                                 args=(device, self.scheme_handler.paillier, type))
            t.start()
            return "Intersection with " + device + " - Paillier - OPE - Thread started, check logs"
        return "Device not found - Have the peer send an ACK first"

    def dj_intersection_first_step_ope(self, device, type="PSI"):
        if device in self.devices:
            t = threading.Thread(target=self.scheme_handler.intersection_first_step_ope,
                                 args=(device, self.scheme_handler.damgard_jurik, type))
            t.start()
            return "Intersection with " + device + " - Damgard-Jurik - OPE - Thread started, check logs"
        return "Device not found - Have the peer send an ACK first"

    def launch_test(self, device):
        if device in self.devices:
            t = threading.Thread(target=self.scheme_handler.test_launcher, args=device)
            t.start()
            return "A thread is launching a massive test with " + device + " - Check logs"
        return "Device not found"
