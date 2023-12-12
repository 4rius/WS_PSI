import random

import zmq
import threading
import time
import socket
import platform

from flaskr.implementations.Paillier import generate_keys, encrypt, calculate_intersection


class Node:
    def __init__(self, id, port, peers):
        self.running = True  # Saber si el nodo está corriendo por si queremos desconectarnos en algún momento
        self.id = id  # IP local
        self.port = port  # Puerto local
        self.peers = peers  # Lista de peers
        self.context = zmq.Context()  # Contexto de ZMQ
        self.router_socket = self.context.socket(zmq.ROUTER)  # Socket ROUTER
        self.devices = {}  # Dispositivos conectados
        self.keys = {}  # Claves públicas de los dispositivos conectados, puede que no haga falta porque se pueden pedir
        self.pkey = None  # Clave privada del nodo
        self.skey = None  # Clave pública del nodo
        self.myData = []  # Datos del nodo, empezamos con números aleatorios

    def start(self):
        print(f"Node {self.id} (You) starting...")
        # Por defecto se generan las claves del nodo usando la implementación de Paillier de phe
        self.pkey, self.skey = generate_keys()
        print(f"Node {self.id} (You) - Keys generated - Objects: {self.pkey} - {self.skey}")

        # Generamos 20 números aleatorios para empezar
        for i in range(20):
            self.myData.append(random.randint(0, 100))
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
                dealer_socket.send_string(f"Hello from Node {self.id}")
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
            if message.startswith("Hello from Node"):
                peer = message.split(" ")[3]
                # Si el dispositivo no está en la lista, agregarlo, útil cuando se implemente el descubrimiento
                if peer not in self.devices:
                    dealer_socket = self.context.socket(zmq.DEALER)
                    dealer_socket.connect(f"tcp://{peer}:{self.port}")
                    self.devices[peer] = {"socket": dealer_socket, "last_seen": day_time}
                    print(f"Added {peer} to my network")
                # Actualizar la lista de dispositivos
                self.devices[peer]["last_seen"] = day_time
                self.devices[peer]["socket"].send_string(f"Added {peer} to my network - From Node {self.id}")
            elif message.endswith("is pinging you!"):
                peer = message.split(" ")[0]
                self.devices[peer]["last_seen"] = day_time
                # Se manda con el router_socket para que lo pueda consumir ping_devices y no lo consuma el router del
                # peer
                self.router_socket.send_multipart([sender, f"{self.id} is up and running!".encode('utf-8')])
            elif message.startswith("Added "):
                peer = message.split(" ")[8]
                self.devices[peer]["last_seen"] = day_time
            # Si recibe un json, es que el peer quiere calcular la intersección
            elif message.startswith("["):
                # Recibimos el json y sacamos el peer, el esquema y los datos
                peer_data = self.router_socket.recv_json()
                # El peer es un dato del json que viene como 'peer'
                peer = peer_data.pop('peer')
                # El esquema es un dato del json que viene como 'scheme', será útil cuando se implementen más esquemas
                scheme = peer_data.pop('scheme')
                print(f"Node {self.id} (You) - Calculating intersection with {peer} - Paillier")
                # Pasamos los datos del peer a una lista
                peer_data_list = []
                for i in range(len(peer_data)):
                    peer_data_list[i] = peer_data[i]
                # Llamamos al método de intersección
                print(calculate_intersection(self.myData, peer_data_list, self.skey))
                # Rezamos
                # Aquí irá el código para enviar la intersección resultante al peer
            else:
                print(f"{self.id} (You) received: {message} but don't know what to do with it")
                peer = message.split(" ")[0]
                self.devices[peer]["last_seen"] = day_time
        self.router_socket.close()
        self.router_socket.unbind(f"tcp://*:{self.port}")
        self.context.term()

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

    def paillier_intersection(self, device):
        # Se cifra el conjunto de datos del nodo y se envía al peer
        if device in self.devices:
            print(f"Node {self.id} (You) - Intersection with {device} - Paillier")
            # Cifrar los datos del nodo
            encrypted_data = []
            for i in range(len(self.myData)):
                enc = encrypt(self.pkey, self.myData[i])
                # Llamar al método ciphertext para obtener el valor cifrado
                encrypted_value = enc.ciphertext()  # Asegúrate de que esto es un método y no una propiedad
                # Convertir el valor cifrado a una representación serializable
                encrypted_data.append({'ciphertext': str(encrypted_value), 'exponent': str(enc.exponent)})
            # Enviar los datos cifrados al peer y añadimos el esquema y el peer al mensaje
            encrypted_data.append({'scheme': 'Paillier', 'peer': self.id})
            self.devices[device]["socket"].send_json(encrypted_data)
            # Recibir los datos cifrados del peer
            # peer_data = self.devices[device]["socket"].recv_json()
            # Descifrar los datos del peer
            # decrypted_data = [self.skey.decrypt(x) for x in peer_data]
            # Calcular la intersección
            # intersection = list(set(self.myData).intersection(set(decrypted_data)))
            # print(f"Node {self.id} (You) - Intersection with {device} - Result: {intersection}")
            # return intersection
            return "Intersection with " + device + " - Paillier"
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

    def get_device_pubkey(self, device):
        if device in self.keys:
            return self.keys[device]
        else:
            return "Device not found"


def get_local_ip():
    system = platform.system()

    # macOS y Linux
    if system == "Linux" or system == "Darwin":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 80))  # No tiene ni que ser un host real
            ip = s.getsockname()[0]
            s.close()
            # Si es ipv6 la tenemos que devolver entre corchetes
            if ":" in ip:
                return "[" + ip + "]"
            return ip
        except OSError:
            print("Error fetching IP, using loopback")
    # Windows y errores de macOS y Linux tiran por aquí
    ip = socket.gethostbyname(socket.gethostname())
    if ":" in ip:
        return "[" + ip + "]"
    return ip
