import unittest
from unittest.mock import MagicMock

import zmq

from Network.Node import Node


class NodeTests(unittest.TestCase):
    def setUp(self):
        Node._Node__instance = None  # Borramos la instancia anterior porque es un singleton
        self.node = Node('192.168.1.1', 5000, ['192.168.1.2', '192.168.1.3'])
        # Mockeamos el socket para no enviar una respuesta
        self.node.router_socket.send_multipart = MagicMock()

    def test_handle_ping_updates_last_seen(self):
        sender = '192.168.1.2'
        message = '192.168.1.2 is pinging you!'
        day_time = '12:00:00'
        self.node.handle_ping(sender, message, day_time)
        self.assertEqual(self.node.devices[sender]['last_seen'], day_time)

    def test_handle_discover_ack_adds_new_peer(self):
        message = 'DISCOVER_ACK: Node 192.168.1.4 acknowledges node 192.168.1.1'
        day_time = '12:00:00'
        self.node.handle_discover_ack(message, day_time)
        self.assertIn('192.168.1.4', self.node.devices)

    def test_ping_device_returns_ok_when_device_responds(self):
        self.node.new_peer('192.168.1.2', '12:00:00')
        device = '192.168.1.2'
        self.node.devices[device]['socket'].recv_string = MagicMock(return_value='192.168.1.2 is up and running!')
        result = self.node.ping_device(device)
        self.assertEqual(result, device + ' - Ping OK')

    def test_ping_device_returns_fail_when_device_does_not_respond(self):
        self.node.new_peer('192.168.1.2', '12:00:00')
        device = '192.168.1.2'
        # Receive nothing
        self.node.devices[device]['socket'].recv_string = MagicMock(side_effect=zmq.error.Again)
        result = self.node.ping_device(device)
        self.assertEqual(result, device + ' - Ping FAIL - Device likely disconnected')

    def test_broadcast_message_sends_message_to_all_devices(self):
        message = 'Hello, nodes!'
        for device in self.node.devices.values():
            device['socket'].send_string = MagicMock()
        self.node.broadcast_message(message)
        for device in self.node.devices.values():
            device['socket'].send_string.assert_called_once_with(message)

    def test_stop_closes_all_device_sockets(self):
        for device in self.node.devices.values():
            device['socket'].close = MagicMock()
        self.node.stop()
        for device in self.node.devices.values():
            device['socket'].close.assert_called_once()

    def test_new_peer_adds_peer_to_devices(self):
        peer = '192.168.1.4'
        last_seen = '12:00:00'
        self.node.new_peer(peer, last_seen)
        self.assertIn(peer, self.node.devices)
        self.assertEqual(self.node.devices[peer]['last_seen'], last_seen)

    def test_discover_peers_does_not_add_yourself(self):
        self.node.context.socket = MagicMock()
        self.node.discover_peers()
        self.assertNotIn('192.168.1.1', self.node.devices)
