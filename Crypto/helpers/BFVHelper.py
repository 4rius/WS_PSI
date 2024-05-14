import random

from Crypto.helpers.CSHelper import CSHelper
from Network.collections.DbConstants import DEFL_DOMAIN
from bfv.batch_encoder import BatchEncoder
from bfv.bfv_decryptor import BFVDecryptor
from bfv.bfv_encryptor import BFVEncryptor
from bfv.bfv_evaluator import BFVEvaluator
from bfv.bfv_key_generator import BFVKeyGenerator
from bfv.bfv_parameters import BFVParameters
from bfv.bfv_relin_key import BFVRelinKey
from util.ciphertext import Ciphertext
from util.polynomial import Polynomial
from util.public_key import PublicKey


def find_min_degree():
    # Buscar el grado que cumple la condición (modulus - 1) % order == 0 donde order es el grado * 2
    for i in range(2, DEFL_DOMAIN // 2 + 1):
        # Comprobar que i es una potencia de 2
        if (DEFL_DOMAIN - 1) % (i * 2) == 0 and (i & (i - 1)) == 0:
            print("Grado mínimo encontrado: ", i)
            return i

    raise ValueError("No se encontró un grado válido para el dominio por defecto")


def reconstruct_relin_key(relin_key):
    keys = [[Polynomial(**poly_dict) for poly_dict in key_tuple] for key_tuple in relin_key['keys']]
    keys = tuple(keys)
    return BFVRelinKey(int(relin_key['base']), keys)


class BFVHelper(CSHelper):

    def __init__(self):
        super().__init__()
        self.imp_name = "BFV"
        self.min_degree = find_min_degree()
        self.params = BFVParameters(poly_degree=self.min_degree, plain_modulus=DEFL_DOMAIN, ciph_modulus=8000000000000)
        self.public_key, self.secret_key, self.relin_key = None, None, None
        self.encoder = None
        self.encryptor = None
        self.decryptor = None
        self.evaluator = None
        self.generate_keys()

    def generate_keys(self, bit_length=None):
        key_generator = BFVKeyGenerator(self.params)
        self.public_key = key_generator.public_key
        self.secret_key = key_generator.secret_key
        self.relin_key = key_generator.relin_key
        self.encoder = BatchEncoder(self.params)
        self.encryptor = BFVEncryptor(self.params, self.public_key)
        self.decryptor = BFVDecryptor(self.params, self.secret_key)
        self.evaluator = BFVEvaluator(self.params)

    def encrypt(self, data):
        return self.encryptor.encrypt(self.encoder.encode([data, 0]))

    def decrypt(self, data):
        return self.encoder.decode(self.decryptor.decrypt(data))[0]

    def serialize_public_key(self):
        public_key_dict = {
            "p0": self.public_key.p0.to_dict(),
            "p1": self.public_key.p1.to_dict(),
            "relin_key": self.relin_key.to_dict()
        }
        return public_key_dict

    def reconstruct_public_key(self, public_key_dict):
        p0 = Polynomial(**public_key_dict["p0"])
        p1 = Polynomial(**public_key_dict["p1"])
        pubkey = PublicKey(p0, p1)
        relin_key = reconstruct_relin_key(public_key_dict["relin_key"])
        # Devolvemos un tuple para que sea compatible con el resto de las funciones
        custom_pubkey = (pubkey, relin_key)
        return custom_pubkey

    def get_ciphertext(self, encrypted_number):
        return encrypted_number.to_dict()

    def get_encrypted_list(self, serialized_encrypted_list, public_key=None):
        enc_list = []
        for element in serialized_encrypted_list:
            c0 = Polynomial(**element["c0"])
            c1 = Polynomial(**element["c1"])
            enc_list.append(Ciphertext(c0, c1))
        return enc_list

    def eval_coefficients(self, coeffs, public_key, my_data):
        enc_eval = []
        f_relin_key = public_key[1]
        f_pubkey = public_key[0]
        f_encryptor = BFVEncryptor(self.params, f_pubkey)
        for x in my_data:
            eval_crypt = self.naive_eval_crypt(coeffs, x, f_relin_key, f_encryptor)
            enc_eval.append(eval_crypt)
        return enc_eval

    def naive_eval_crypt(self, coeffs, x, relin_key, encryptor):
        result = coeffs[0]

        for pos, coef in enumerate(coeffs[1:]):
            encrypt_x = encryptor.encrypt(self.encoder.encode([x ** (pos + 1), 0]))

            termino = self.evaluator.multiply(encrypt_x, coef, relin_key)

            result = self.evaluator.add(result, termino)

        rb = random.randint(1, self.params.plain_modulus)

        temp = self.evaluator.multiply(result, encryptor.encrypt(self.encoder.encode([rb, 0])), relin_key)

        return self.evaluator.add(temp, encryptor.encrypt(self.encoder.encode([x, 0])))

    def serialize_result(self, result, type):
        return [ciphertext.to_dict() for ciphertext in result]
