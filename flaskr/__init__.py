import os
import socket

from flask import Flask, render_template, jsonify
from . import db
from . import network
from .network import Node


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
    peers = ["192.168.1.49:5001", "192.168.1.3:5001", "192.168.1.4:5001"]
    local_ip = socket.gethostbyname(socket.gethostname())
    node = Node(local_ip, 5001, peers)
    node.start()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/metrics')
    def metrics():
        return render_template('metrics.html')

    @app.route('/api/devices')
    def api_devices():
        return jsonify(node.get_devices())

    @app.route('/api/ping/<device>')
    def api_ping(device):
        return jsonify({'status': node.ping_device(device)})

    return app
