import random

from damgard_jurik import keygen, EncryptedNumber, PublicKey

from Network.collections.DbConstants import DEFL_KEYSIZE, DEFL_EXPANSIONFACTOR
from Network.helpers.CSHelper import CSHelper


class DamgardJurikHelper(CSHelper):

    def __init__(self):
        self.private_key_ring = None
        self.public_key = None
        self.public_key, self.private_key_ring = self.generate_keys()
        self.imp_name = "Damgard-Jurik"

    def generate_keys(self):
        public_key, private_key_ring = keygen(n_bits=DEFL_KEYSIZE, s=DEFL_EXPANSIONFACTOR, threshold=1, n_shares=1)
        return public_key, private_key_ring

    def encrypt(self, number):
        return self.public_key.encrypt(number)

    def decrypt(self, number):
        return self.private_key_ring.decrypt(number)

    def serialize_public_key(self):
        public_key_dict = {
            'n': str(self.public_key.n),
            's': str(self.public_key.s),
            'm': str(self.public_key.m),
            'threshold': str(self.public_key.threshold),
            'delta': str(self.public_key.delta)
        }
        return public_key_dict

    def reconstruct_public_key(self, public_key_dict):
        # Si proviene de un dispositivo Android, no traerá ni m, threshold ni delta, por lo que los marcaremos a 1
        # por defecto, no hacen falta para el cifrado
        if 'm' not in public_key_dict:
            return PublicKey(int(public_key_dict['n']), int(public_key_dict['s']), 1, 1, 1)
        return PublicKey(int(public_key_dict['n']), int(public_key_dict['s']), int(public_key_dict['m']),
                         int(public_key_dict['threshold']), int(public_key_dict['delta']))

    def get_encrypted_set(self, serialized_encrypted_set, public_key):
        return {element: EncryptedNumber(ciphertext, public_key) for element, ciphertext in
                serialized_encrypted_set.items()}

    def get_encrypted_list(self, serialized_encrypted_list, public_key):
        return [EncryptedNumber(ciphertext, public_key) for ciphertext in serialized_encrypted_list]

    def get_encrypted_list_f(self, serialized_encrypted_list):
        return [EncryptedNumber(int(ciphertext), self.public_key) for ciphertext in serialized_encrypted_list]

    def encrypt_my_data(self, my_set, domain):
        return {element: self.public_key.encrypt(1) if element in my_set else self.public_key.encrypt(0) for element in
                range(domain)}

    def recv_multiplied_set(self, serialized_multiplied_set, public_key):
        print("Recibimos el set A multiplicado por 0 o por 1 dependiendo de si están en el set B")
        return {element: EncryptedNumber(int(ciphertext), public_key) for element, ciphertext in
                serialized_multiplied_set.items()}

    def get_multiplied_set(self, enc_set, node_set):
        print("Multiplicamos por 0 o por 1 los elementos del set A dependiendo de si están en el set B")
        result = {}
        for element, encrypted_value in enc_set.items():
            multiplier = int(int(element) in node_set)
            result[element] = EncryptedNumber(encrypted_value.value * multiplier, encrypted_value.public_key)
        return result

    def intersection_enc_size(self, multiplied_set):
        return sum([int(element.value) for element in multiplied_set.values()])

    def get_ciphertext(self, encrypted_number):
        return str(encrypted_number.value)

    """ OPE stuff """

    def horner_encrypted_eval(self, coefs, x):
        result = coefs[-1]
        for coef in reversed(coefs[:-1]):
            result = coef + x * result
        return result

    def eval_coefficients(self, coefs, pubkey, my_data):
        print("Evaluamos el polinomio en los elementos del set B")
        encrypted_results = []
        for element in my_data:
            rb = random.randint(1, 1000)
            Epbj = self.horner_encrypted_eval(coefs, element)
            encrypted_results.append(pubkey.encrypt(element) + rb * Epbj)
        return encrypted_results

    def get_evaluations(self, coefs, pubkey, my_data):
        print("Evaluamos el polinomio en los elementos del set B")
        evaluations = []
        for element in my_data:
            rb = random.randint(1, 1000)
            Epbj = self.horner_encrypted_eval(coefs, element)
            evaluations.append(pubkey.encrypt(0) + rb * Epbj)
        return evaluations

    def serialize_result(self, result, type=None):
        return [str(element.value) for element in result] if type == "OPE" else \
            {element: str(encrypted_value.value) for element, encrypted_value in result.items()}
