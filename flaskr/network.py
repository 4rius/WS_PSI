from datetime import datetime
from time import sleep
import zmq
import json
import threading

data = {}
connected_devices = {}


def start_network():
    # Crear contexto ZMQ
    context = zmq.Context()
    # Crear socket de tipo REP (Response)
    socket = context.socket(zmq.REP)
    # Vincular socket al puerto 5555 (en localhost)
    socket.bind("tcp://*:5555")

    def check_device(context, device):
        while True:
            try:
                # Socket para enviar la solicitud al dispositivo en específico
                check_socket = context.socket(zmq.REQ)
                check_socket.connect(f"tcp://{device}:5555")
                check_socket.send(b"CHECK")

                # Añadir un tiempo de espera al socket
                check_socket.setsockopt(zmq.RCVTIMEO, 5000)

                # Traza de log: Fecha - Hora - Dispositivo - Estado
                date = datetime.now().strftime("%d/%m/%Y")
                time = datetime.now().strftime("%H:%M:%S")
                print(f"{date} - {time} - {device} - SEND CHECK")

                if check_socket.recv() == b"OK":
                    print(f"{device} - OK")
                    connected_devices[device] = True
                else:
                    print(f"{device} - FAIL")
                    connected_devices[device] = False
                sleep(5)
            except zmq.Again as e:
                print(f"{device} - FAIL - {e} - Device may be disconnected")
                connected_devices[device] = False
                return
            except Exception as e:
                print(f"{device} - FAIL - {e}")
                connected_devices[device] = False
                return

    def handle_requests():
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        while True:
            socks = dict(poller.poll())
            if socket in socks and socks[socket] == zmq.POLLIN:
                message = socket.recv()
                # Remove the b'' from the message
                message = message.decode("utf-8")
                print(f"Received request: {message}")
                # Add the device to the list of connected devices
                connected_devices[message] = True
                # Start a new thread to check if the device is still connected
                thread_ping = threading.Thread(target=check_device, args=(context, message,))
                thread_ping.start()

    # Iniciar un hilo para manejar las solicitudes
    thread = threading.Thread(target=handle_requests)
    thread.start()


def get_data():
    return json.dumps({'data': 'data'})


def get_devices():
    devices = []
    for device, is_connected in connected_devices.items():
        if is_connected:
            devices.append(device)
    return json.dumps({'devices': devices})
