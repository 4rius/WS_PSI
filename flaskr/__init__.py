import os

from flask import Flask, render_template, jsonify, request

from . import Node, Logs
from .Node import Node
from .helpers import networking


def create_app(test_config=None):
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

    # Inicializar el nodo
    # Peers hardcodeados para probar su funcionamiento
    peers = ["192.168.1.135:5001", "[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:5001"]
    # Get the local IP and not the loopback
    local_ip = networking.get_local_ip()
    node = Node(local_ip, 5001, peers)
    node.start()
    Logs.setup_logs(node.id, len(node.myData), node.domain)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/metrics')
    def metrics():
        return render_template('metrics.html')

    @app.route('/api/devices', methods=['GET'])
    def api_devices():
        return jsonify(node.get_devices())

    @app.route('/api/ping/<device>', methods=['POST'])
    def api_ping(device):
        return jsonify({'status': node.ping_device(device)})

    @app.route('/api/port', methods=['GET'])
    def api_port():
        if not node.running:
            return jsonify({'port': "Not connected to the network"})
        return jsonify({'port': node.port})

    @app.route('/api/disconnect', methods=['POST'])
    def api_disconnect():
        node.stop()
        return jsonify({'status': 'Disconnected from the network'})

    @app.route('/api/connect', methods=['POST'])
    def api_connect():
        node.start()
        return jsonify({'status': 'Found peers and connected to the network'})

    @app.route('/api/mykeys', methods=['GET'])
    def api_pubkey():
        return jsonify({'pubkeyN': str(node.scheme_handler.paillier.public_key.n),
                        'pubkeyG': str(node.scheme_handler.paillier.public_key.g),
                        'privkeyP': str(node.scheme_handler.paillier.public_key.p),
                        'privkeyQ': str(node.scheme_handler.paillier.public_key.q)})

    @app.route('/api/intersection', methods=['POST'])
    def api_ca_dj():
        device = request.args.get('device')
        scheme = request.args.get('scheme')
        type = request.args.get('type')
        if type is None:
            return jsonify({'status': node.start_intersection(device, scheme)})
        return jsonify({'status': node.start_intersection(device, scheme, type)})

    @app.route('/api/dataset', methods=['GET'])
    def api_dataset():
        return jsonify({'dataset': list(node.myData)})

    @app.route('/api/id', methods=['GET'])
    def api_id():
        return jsonify({'id': node.id})

    @app.route('/api/results', methods=['GET'])
    def api_result():
        return jsonify({'result': node.results})

    @app.route('/api/genkeys', methods=['POST'])
    def api_genkeys():
        scheme = request.args.get('scheme')
        return jsonify({'status': node.genkeys(scheme)})

    @app.route('/api/discover_peers', methods=['POST'])
    def api_discover_peers():
        return jsonify({'status': node.discover_peers()})

    @app.route('/api/logs', methods=['GET'])
    def api_metrics():
        id = request.args.get('id')
        if id is not None:
            return Logs.get_logs(id)
        return Logs.get_logs(node.id)

    @app.route('/api/test', methods=['POST'])
    def api_test():
        device = request.args.get('device')
        return jsonify({'status': node.launch_test(device)})

    return app
