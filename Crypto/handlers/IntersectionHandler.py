class IntersectionHandler:
    def __init__(self, id, my_data, domain, devices, results):
        # Añadimos las variables de instancia de la clase Node para facilitar el acceso a los datos
        self.id = id
        self.my_data = my_data
        self.domain = domain
        self.devices = devices
        self.results = results

    def send_message(self, peer, ser_enc_res, implementation, peer_pubkey=None):
        if peer_pubkey:
            message = {'data': ser_enc_res, 'implementation': implementation, 'peer': self.id,
                       'pubkey': peer_pubkey, 'step': '2'}
        else:
            message = {'data': ser_enc_res, 'implementation': implementation, 'peer': self.id, 'step': 'F'}
        self.devices[peer]["socket"].send_json(message)

    def intersection_first_step(self, device, cs):
        raise NotImplementedError

    def intersection_second_step(self, device, cs, peer_data, pubkey):
        raise NotImplementedError

    def intersection_final_step(self, device, cs, peer_data):
        raise NotImplementedError
