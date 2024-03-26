import functools
import os

from flask import Flask, render_template, jsonify, request

from Network import Logs
from Network.Node import Node
from Network.collections import networking
from Network.collections.networking import is_valid_ipv4, is_valid_ipv6
from Crypto.helpers.CryptoImplementation import CryptoImplementation


def node_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        node = Node.getinstance()
        if node is None:
            return jsonify({'status': 'Node not connected'})
        return func(node, *args, **kwargs)

    return wrapper


def create_app(test_config=None):
    def create_node():
        peers = ["192.168.1.135:5001", "[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:5001"]
        local_ip = networking.get_local_ip()

        node = Node(local_ip, 5001, peers)
        node.start()
        Logs.setup_logs(node.id, len(node.myData), node.domain)
    create_node()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/metrics')
    def metrics():
        return render_template('metrics.html')

    @app.route('/api/devices', methods=['GET'])
    @node_wrapper
    def api_devices(node):
        return jsonify(node.get_devices())

    @app.route('/api/ping/<device>', methods=['POST'])
    @node_wrapper
    def api_ping(node, device):
        return jsonify({'status': node.ping_device(device)})

    @app.route('/api/port', methods=['GET'])
    @node_wrapper
    def api_port(node):
        if not node.running:
            return jsonify({'port': "Not connected to the network"})
        return jsonify({'port': node.port})

    @app.route('/api/disconnect', methods=['POST'])
    @node_wrapper
    def api_disconnect(node):
        node.stop()
        return jsonify({'status': 'Node destroyed'})

    @app.route('/api/connect', methods=['POST'])
    def api_connect():
        if Node.getinstance() is not None:
            return jsonify({'status': 'Node already connected'})
        create_node()
        return jsonify({'status': 'Node connected'})

    @app.route('/api/mykeys', methods=['GET'])
    @node_wrapper
    def api_pubkey(node):
        return (jsonify({'pubkeyN': str(node.json_handler.CSHandlers[CryptoImplementation.from_string("Paillier")].
                                        public_key.n),
                         'pubkeyG': str(node.json_handler.CSHandlers[CryptoImplementation.from_string("Paillier")].
                                        public_key.g),
                         'pubkeyNDJ': str(node.json_handler.
                                          CSHandlers[CryptoImplementation.from_string("DamgardJurik")].public_key.n),
                         'pubkeySDJ': str(node.json_handler.
                                          CSHandlers[CryptoImplementation.from_string("DamgardJurik")].public_key.s),
                         'pubkeyMDJ': str(node.json_handler.
                                          CSHandlers[CryptoImplementation.from_string("DamgardJurik")].public_key.m)}))

    @app.route('/api/intersection', methods=['POST'])
    @node_wrapper
    def api_intersection(node):
        device = request.args.get('device')
        scheme = request.args.get('scheme')
        type = request.args.get('type')
        if device is None or scheme is None or type is None:
            return jsonify({'status': 'Invalid parameters'})
        return jsonify({'status': node.start_intersection(device, scheme, type)})

    @app.route('/api/dataset', methods=['GET'])
    @node_wrapper
    def api_dataset(node):
        return jsonify({'dataset': list(node.myData)})

    @app.route('/api/id', methods=['GET'])
    @node_wrapper
    def api_id(node):
        return jsonify({'id': node.id})

    @app.route('/api/results', methods=['GET'])
    @node_wrapper
    def api_result(node):
        return jsonify({'result': node.results})

    @app.route('/api/genkeys', methods=['POST'])
    @node_wrapper
    def api_genkeys(node):
        scheme = request.args.get('scheme')
        return jsonify({'status': node.genkeys(scheme)})

    @app.route('/api/discover_peers', methods=['POST'])
    @node_wrapper
    def api_discover_peers(node):
        return jsonify({'status': node.discover_peers()})

    @app.route('/api/add_peer', methods=['POST'])
    @node_wrapper
    def api_add_peer(node):
        peer = request.args.get('peer')
        if is_valid_ipv4(peer) or is_valid_ipv6(peer):
            return jsonify({'status': node.new_peer(peer, "Not seen yet")})
        return jsonify({'status': 'Invalid IPv4 or IPv6 address'})

    @app.route('/api/logs', methods=['GET'])
    @node_wrapper
    def api_metrics(node):
        id = request.args.get('id')
        if id is not None:
            return Logs.get_logs(id)
        return Logs.get_logs(node.id)

    @app.route('/api/test', methods=['POST'])
    @node_wrapper
    def api_test(node):
        device = request.args.get('device')
        return jsonify({'status': node.launch_test(device)})

    return app
