import zmq
import json
import threading
import time


class Node:
    def __init__(self, id, port, peers):
        self.id = id  # IP local
        self.port = port  # Puerto local
        self.peers = peers  # Lista de peers (después se puede cambiar por un discovery service)
        self.context = zmq.Context()  # Contexto de ZMQ
        self.router_socket = self.context.socket(zmq.ROUTER)  # Socket ROUTER - Escuchar conexiones entrantes
        self.dealer_socket = self.context.socket(zmq.DEALER)  # Socket DEALER - Conectar a otros nodos
        self.devices = {}  # Diccionario de dispositivos conectados

    def start(self):
        # Iniciar los sockets en threads separados, para que no se bloquee el main thread
        threading.Thread(target=self.start_router_socket).start()
        threading.Thread(target=self.start_dealer_socket).start()

    def start_router_socket(self):
        # Iniciar el socket ROUTER
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
            # Si el mensaje es de bienvenida, agregamos el peer a nuestra lista de dispositivos
            if message.startswith("Hello from Node"):
                peer = message.split(" ")[3]
                self.devices[peer] = "Last seen: " + day_time
                # Enviar mensaje de bienvenida al peer
                self.dealer_socket.send_string(f"Added {peer} to my network - From Node {self.id}")
            # Si el mensaje es de ping, respondemos que estamos conectados
            elif message.endswith("is pinging you!"):
                peer = message.split(" ")[0]
                self.devices[peer] = "Last seen: " + day_time
                # Send the reply to that specific peer
                self.router_socket.send_multipart([peer.encode('utf-8'), f"{self.id} is up and running!".encode('utf-8')])
            elif message.startswith("Added "):
                peer = message.split(" ")[1]
                self.devices[peer] = "Last seen: " + day_time
            # Si el mensaje no es de bienvenida ni de ping, es un mensaje de otro nodo, simplemente lo reenviamos
            else:
                self.dealer_socket.send_string(f"{self.id} received: {message} but doesn't know what to do with it")

    def start_dealer_socket(self):
        # Intentar conectarse a todos los peers de la lista, el que no esté en nuestra lista de dispositivos se agrega y se le envía un mensaje de bienvenida
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
            attempts = 0
            while attempts < 3:  # Intenta el ping 3 veces
                self.dealer_socket.send_string(f"{self.id} is pinging you!")
                try:
                    reply = self.router_socket.recv(flags=zmq.NOBLOCK)
                    try:
                        reply = reply.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                    if reply == f"{device} is up and running!":
                        print(f"{device} - Ping OK")
                        return device + " - Ping OK"
                except zmq.error.Again:
                    print(f"{device} - Ping FAIL - Retrying...")
                    time.sleep(1.5)  # Esperar antes de intentar de nuevo
                attempts += 1
            print(f"Device {device} - Ping FAIL - Device may have been disconnected")
            self.devices[device] = False
            return device + " - Ping FAIL - Device likely disconnected"
        else:
            print("Device not found")
            return "Device not found"

    def join(self):
        try:
            self.router_socket.close()
            self.dealer_socket.close()
        finally:
            self.context.term()
