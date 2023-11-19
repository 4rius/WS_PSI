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
            # Desde la pequeña webapp quiero añadir el eleminar dispositivos, timestamp de cuando se conectaron y un botón para enviarles un ping
    return json.dumps({'devices': devices})
