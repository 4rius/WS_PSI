import random

from bfv.batch_encoder import BatchEncoder
from bfv.bfv_decryptor import BFVDecryptor
from bfv.bfv_encryptor import BFVEncryptor
from bfv.bfv_evaluator import BFVEvaluator
from bfv.bfv_key_generator import BFVKeyGenerator
from bfv.bfv_parameters import BFVParameters
from util.polynomial import Polynomial

plain_modulus = 14293
domain = 10

elementos_A = {2, 1, 4, 7, 9}  # tienen que ser menor que plain_modulus

elementos_B = {1, 4, 5, 6, 9}  # tienen que ser menor que plain_modulus


def encrypt_my_data(data, encryptor, encoder):
    return {element: encryptor.encrypt(encoder.encode([1, 0])) if element in data else encryptor.encrypt(encoder.encode([0, 0])) for element in range(domain)}


def get_multiplied_set(enc_A, elementos_B, evaluator, relin_key, encoder, encryptor):
    result = {}
    for element, enc_value in enc_A.items():
        multiplier = int(element) in elementos_B
        if multiplier is False:
            result[element] = encryptor.encrypt(encoder.encode([0, 0]))
        else:
            result[element] = evaluator.multiply(enc_value, encryptor.encrypt(encoder.encode([2, 0])), relin_key)
    return result


def main():
    degree = 2

    ciph_modulus = 8000000000000

    params = BFVParameters(poly_degree=degree,

                           plain_modulus=plain_modulus,

                           ciph_modulus=ciph_modulus)

    key_generator = BFVKeyGenerator(params)

    public_key = key_generator.public_key

    secret_key = key_generator.secret_key

    relin_key = key_generator.relin_key

    encoder = BatchEncoder(params)

    encryptor = BFVEncryptor(params, public_key)

    decryptor = BFVDecryptor(params, secret_key)

    evaluator = BFVEvaluator(params)

    # Alice
    enc_A = encrypt_my_data(elementos_A, encryptor, encoder)

    # B cifra uin 0 o multiplica homomórficamente por 2
    eval_set = get_multiplied_set(enc_A, elementos_B, evaluator, relin_key, encoder, encryptor)

    # A descifra el resultado, si es un 2, lo añade a la intersección
    resultado = {}
    for element, enc_value in eval_set.items():
        decrypted = decryptor.decrypt(enc_value)
        decrypted = encoder.decode(decrypted)
        resultado[element] = decrypted[0]
    interseccion = [element for element in resultado if resultado[element] == 2]
    return interseccion


# Ebi-< Hornel_eval( Ebj)) ->


if __name__ == '__main__':
    for i in range(100):
        res = main()
        # Intersección real
        print("Intersección real: ", [a for a in elementos_A if a in elementos_B])
        if res != [a for a in elementos_A if a in elementos_B]:
            print("Intersección incorrecta en la iteración: ", i)
        print("Intersection: " + str(main()))
        print("#####################")