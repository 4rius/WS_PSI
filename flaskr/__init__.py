import os

from flask import Flask, render_template, jsonify

from . import Node, Logs
from .Node import Node
from . import networking


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
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
    peers = ["192.168.1.135:5001", "172.19.0.4:5001", "172.19.0.3:5001", "172.19.0.65:5001",
             "[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:5001"]
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
        node.join()
        return jsonify({'status': 'Disconnected from the network'})

    @app.route('/api/connect', methods=['POST'])
    def api_connect():
        node.start()
        return jsonify({'status': 'Found peers and connected to the network'})

    @app.route('/api/mykeys', methods=['GET'])
    def api_pubkey():
        return jsonify({'pubkeyN': str(node.pubkey_paillier.n), 'pubkeyG': str(node.pubkey_paillier.g), 'privkeyP': str(node.privkey_paillier.p),
                        'privkeyQ': str(node.privkey_paillier.q)})

    @app.route('/api/int_paillier/<device>', methods=['POST'])
    def api_find_intersection(device):
        return jsonify({'status': node.paillier_intersection_first_step(device)})

    @app.route('/api/int_dj/<device>', methods=['POST'])
    def api_find_intersection_dj(device):
        return jsonify({'status': node.dj_intersection_first_step(device)})

    @app.route('/api/int_paillier_ope/<device>', methods=['POST'])
    def api_find_intersection_ope(device):
        return jsonify({'status': node.paillier_intersection_first_step_ope(device)})

    @app.route('/api/int_dj_ope/<device>', methods=['POST'])
    def api_find_intersection_dj_ope(device):
        return jsonify({'status': node.dj_intersection_first_step_ope(device)})

    @app.route('/api/ca_paillier/<device>', methods=['POST'])
    def api_ca_paillier(device):
        return jsonify({'status': node.paillier_intersection_first_step_ope(device, "PSI-CA")})

    @app.route('/api/dataset', methods=['GET'])
    def api_dataset():
        return jsonify({'dataset': list(node.myData)})

    @app.route('/api/id', methods=['GET'])
    def api_id():
        return jsonify({'id': node.id})

    @app.route('/api/results', methods=['GET'])
    def api_result():
        return jsonify({'result': node.results})

    @app.route('/api/gen_paillier', methods=['POST'])
    def api_gen_paillier():
        return jsonify({'status': node.gen_paillier()})

    @app.route('/api/gen_dj', methods=['POST'])
    def api_gen_dj():
        return jsonify({'status': node.gen_dj()})

    @app.route('/api/discover_peers', methods=['POST'])
    def api_discover_peers():
        return jsonify({'status': node.discover_peers()})

    @app.route('/api/logs', methods=['GET'])
    def api_metrics():
        return Logs.get_logs(node.id)

    return app
