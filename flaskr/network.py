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

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            attempts = 0
            max_attempts = 3

            while attempts < max_attempts:
                self.devices[device]["socket"].send_string(f"{self.id} is pinging you!")

                # Esperar un tiempo antes de intentar recibir la respuesta
                time.sleep(1.5)

                try:
                    reply = self.devices[device]["socket"].recv_string()
                    try:
                        reply = reply.decode('utf-8')
                    except UnicodeDecodeError:
                        continue

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
                    attempts += 1

            print(f"Device {device} - Ping FAIL - Device likely disconnected")
            self.devices[device]["last_seen"] = False
            return device + " - Ping FAIL - Device likely disconnected"
        else:
            print("Device not found")
            return "Device not found"

    def get_devices(self):
        return {device: info["last_seen"] for device, info in self.devices.items()}

    import zmq

    # ...

    def ping_device(self, device):
        if device in self.devices:
            print(f"Pinging device: {device}")
            attempts = 0
            max_attempts = 3
            timeout = 1500  # Tiempo máximo de espera
            poller = zmq.Poller()

            poller.register(self.devices[device]["socket"], zmq.POLLIN)

            while attempts < max_attempts:
                self.devices[device]["socket"].send_string(f"{self.id} is pinging you!")

                # Esperar hasta que haya algo para leer o hasta que se alcance el tiempo máximo de espera
                events = dict(poller.poll(timeout))

                if self.devices[device]["socket"] in events:
                    reply = self.devices[device]["socket"].recv_string()
                    try:
                        reply = reply.decode('utf-8')
                    except UnicodeDecodeError:
                        continue

                    print(f"{device} - Received: {reply}")

                    if reply:
                        self.devices[device]["last_seen"] = time.strftime("%H:%M:%S", time.localtime())
                        print(f"{device} - Ping OK")
                        return device + " - Ping OK"
                    else:
                        print(f"{device} - Ping FAIL - Empty response")
                        return device + " - Ping FAIL - Empty response"

                print(f"{device} - Ping FAIL - Retrying...")
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
