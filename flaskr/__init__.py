import functools
import os

from flask import Flask, render_template, jsonify, request
from flask.views import MethodView

from Logs import Logs
from Network.Node import Node
from Network.collections import networking
from Network.collections.DbConstants import DEFL_PORT, print_banner
from Network.collections.networking import is_valid_ipv4, is_valid_ipv6
from Crypto.helpers.CryptoImplementation import CryptoImplementation


def node_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        node = Node.getinstance()
        if node is None:
            return jsonify({'status': 'The node is not running. Connect to the network first'})
        return func(node, *args, **kwargs)

    return wrapper


def create_app(test_config=None):
    print("The service is starting...")

    def create_node(port=DEFL_PORT):
        peers = ["192.168.1.135", "[2001:0db8:85a3:0000:0000:8a2e:0370:7334]"]
        local_ip = networking.get_local_ip()

        node = Node(local_ip, port, peers)
        node.start()
        Logs.setup_logs(node.id, len(node.myData), node.domain)

    create_node()
    print_banner()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

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
        port = request.args.get('port')
        if Node.getinstance() is not None:
            return jsonify({'status': 'Node already connected'})
        if port is None or not port.isdigit():
            create_node()
        else:
            create_node(port)
        return jsonify({'status': 'Node connected using port ' + str(port) if port is not None else
        'Node connected using port ' + str(DEFL_PORT)})

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
        data = request.get_json()
        device = data.get('device')
        scheme = data.get('scheme')
        type = data.get('type')
        rounds = data.get('rounds')
        if device is None or scheme is None or type is None:
            return jsonify({'status': 'Invalid parameters'})
        if rounds is None or not str(rounds).isdigit():
            rounds = 1
        return jsonify({'status': node.start_intersection(device, scheme, type, rounds)})

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
        bit_length = request.args.get('bit_length')
        if scheme is None:
            return jsonify({'status': 'Invalid parameters'})
        if not bit_length.isdigit():
            return jsonify({'status': 'Invalid bit length'})
        return jsonify({'status': node.genkeys(scheme, int(bit_length))})

    @app.route('/api/discover_peers', methods=['POST'])
    @node_wrapper
    def api_discover_peers(node):
        return jsonify({'status': node.discover_peers()})

    @app.route('/api/add', methods=['PUT'])
    @node_wrapper
    def api_add_peer(node):
        peer = request.args.get('peer')
        if peer is None:
            return jsonify({'status': 'Invalid parameters - No peer provided'})
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

    @app.route('/api/setup', methods=['POST'])
    @node_wrapper
    def api_setup(node):
        domain = request.args.get('domain')
        set_size = request.args.get('set_size')
        if domain is None or set_size is None:
            return jsonify({'status': 'Invalid parameters'})
        res = node.update_setup(domain, set_size)
        if res == "Setup updated":
            Logs.setup_logs(node.id, set_size, domain)
        return jsonify({'status': res})

    @app.route('/api/check_connection', methods=['GET'])
    @node_wrapper
    def api_check_connection(node):
        return jsonify({'status': "Up and running!"})

    @app.route('/api/tasks', methods=['GET'])
    @node_wrapper
    def api_check_tasks(node):
        return jsonify({'status': node.check_tasks()})

    # noinspection PyMethodMayBeStatic
    # To be able to use appropriate API methods, GET for status and POST for connect/disconnect
    class FirebaseAPI(MethodView):
        def get(self):
            if Logs.default_app is None:
                return jsonify({'status': 'Firebase not connected - The application will not log data to Firebase'})
            return jsonify({'status': 'Firebase connected'})

        def post(self):
            action = request.args.get('action')
            if action == 'connect':
                return jsonify({'status': Logs.connect_firebase()})
            elif action == 'disconnect':
                return jsonify({'status': Logs.disconnect_firebase()})

    app.add_url_rule('/api/firebase', view_func=FirebaseAPI.as_view('firebase_api'))

    return app
