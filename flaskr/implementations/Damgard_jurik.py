import random

from damgard_jurik import keygen, EncryptedNumber, PublicKey

from flaskr.DbConstants import DEFL_KEYSIZE, DEFL_EXPANSIONFACTOR


def generate_keypair_dj():
    public_key, private_key_ring = keygen(n_bits=DEFL_KEYSIZE, s=DEFL_EXPANSIONFACTOR, threshold=1, n_shares=1)
    return public_key, private_key_ring


def encrypt_dj(public_key, number):
    return public_key.encrypt(number)


def decrypt_dj(private_key_ring, number):
    return private_key_ring.decrypt(number)


def serialize_public_key_dj(public_key):
    public_key_dict = {
        'n': str(public_key.n),
        's': str(public_key.s),
        'm': str(public_key.m),
        'threshold': str(public_key.threshold),
        'delta': str(public_key.delta)
    }
    return public_key_dict


def reconstruct_public_key_dj(public_key_dict):
    # Si proviene de un dispositivo Android, no traerá ni m, threshold ni delta, por lo que los marcaremos a 1 por defecto, no hacen falta para el cifrado
    if 'm' not in public_key_dict:
        return PublicKey(int(public_key_dict['n']), int(public_key_dict['s']), 1, 1, 1)
    return PublicKey(int(public_key_dict['n']), int(public_key_dict['s']), int(public_key_dict['m']),
                     int(public_key_dict['threshold']), int(public_key_dict['delta']))


def get_encrypted_set_dj(serialized_encrypted_set, public_key):
    return {element: EncryptedNumber(ciphertext, public_key) for element, ciphertext in
            serialized_encrypted_set.items()}


def get_encrypted_list_dj(serialized_encrypted_list, public_key):
    return [EncryptedNumber(ciphertext, public_key) for ciphertext in serialized_encrypted_list]


def encrypt_my_data_dj(my_set, public_key, domain):
    return {element: public_key.encrypt(1) if element in my_set else public_key.encrypt(0) for element in range(domain)}


def recv_multiplied_set_dj(serialized_multiplied_set, public_key):
    print("Ciframos los elementos del set A")
    return {element: EncryptedNumber(int(ciphertext), public_key) for element, ciphertext in
            serialized_multiplied_set.items()}


def get_multiplied_set_dj(enc_set, node_set):
    print("Multiplicamos por 0 o por 1 los elementos del set A dependiendo de si están en el set B")
    result = {}
    for element, encrypted_value in enc_set.items():
        multiplier = int(int(element) in node_set)
        result[element] = EncryptedNumber(encrypted_value.value * multiplier, encrypted_value.public_key)
    return result


def intersection_enc_size_dj(multiplied_set):
    return sum([int(element.value) for element in multiplied_set.values()])


""" OPE stuff """


def horner_eval_crypt_dj(coefs, x):
    result = coefs[-1]
    for coef in reversed(coefs[:-1]):
        result = coef + x * result
    return result


def eval_coefficients_dj(coefs, pubkey, my_data):
    print("Evaluamos el polinomio en los elementos del set B")
    encrypted_results = []
    for element in my_data:
        rb = random.randint(1, 1000)
        Epbj = horner_eval_crypt_dj(coefs, element)
        encrypted_results.append(pubkey.encrypt(element) + rb * Epbj)
    return encrypted_results
