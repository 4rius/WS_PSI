import zmq
import json
import threading
import time

class Node:
    def __init__(self, id, port, peers):
        self.id = id                                            # IP local
        self.port = port                                        # Puerto local
        self.peers = peers                                      # Lista de peers (después se puede cambiar por un discovery service)
        self.context = zmq.Context()                            # Contexto de ZMQ
        self.router_socket = self.context.socket(zmq.ROUTER)    # Socket ROUTER - Escuchar conexiones entrantes
        self.dealer_socket = self.context.socket(zmq.DEALER)    # Socket DEALER - Conectar a otros nodos
        self.devices = {}                                       # Diccionario de dispositivos conectados

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
                # Confirmamos la conexión con el peer
                # Respondemos con el router porque el dealer no puede enviar mensajes sin antes recibir uno
                self.router_socket.send_string(f"{self.id} received: {message} and added {peer} to the list of devices")
            # Si el mensaje es de ping, respondemos que estamos conectados
            elif message.endswith("is pinging you!"):
                peer = message.split(" ")[0]
                self.dealer_socket.send_string(f"{self.id} is up and running!")
                self.devices[peer] = "Last seen: " + day_time
            # Si el mensaje no es de bienvenida ni de ping, es un mensaje de otro nodo, simplemente lo reenviamos
            else:
                self.dealer_socket.send_string(f"{self.id} received: {message} but doesn't know what to do with it")

    def start_dealer_socket(self):
        # Intentar conectarse a todos los peers de la lista, el que no esté en nuestra lista de dispositivos se agrega y se le envía un mensaje de bienvenida
        for peer in self.peers:
            print(f"Node {self.id} (You) connecting to Node {peer}")
            self.dealer_socket.connect(f"tcp://{peer}")
            time.sleep(0.5)
            if peer not in self.devices:
                self.dealer_socket.send_string(f"Hello from Node {self.id}")

    def get_devices(self):
        return self.devices

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            for _ in range(3):  # Intenta el ping 3 veces
                self.dealer_socket.send_string(f"{self.id} is pinging you!")
                try:
                    reply = self.router_socket.recv(flags=zmq.NOBLOCK)
                    try:
                        reply = reply.decode('utf-8')
                    except UnicodeDecodeError:
                        continue
                    if reply.endswith("is up and running!"):
                        print(f"Device {device} is still connected")
                        return device + " - Ping OK"
                except zmq.error.Again:
                    time.sleep(1)  # Espera 1 segundo antes de intentar de nuevo
            print(f"Device {device} did not reply, it may have been disconnected")
            self.devices[device] = "Disconnected - You can try to ping it again"
            return device + " - Ping FAIL - Likely disconnected"
        else:
            print("Device not found")
            return "Device not found"

    def join(self):
        try:
            self.router_socket.close()
            self.dealer_socket.close()
        finally:
            self.context.term()
