from collections import defaultdict

from phe import paillier


# Devuelve los objetos clave pública y privada
def generate_keys():
    public_key, private_key = paillier.generate_paillier_keypair()
    return public_key, private_key


def serialize_public_key(public_key):
    # Convertir la clave pública en un diccionario con la n
    public_key_dict = {
        'n': str(public_key.n)
    }
    return public_key_dict


def reconstruct_public_key(public_key_dict):
    # Reconstruir la clave pública a partir del diccionario
    return paillier.PaillierPublicKey(n=int(public_key_dict['n']))


# Cifrar los números de los sets con los que arrancamos
def encrypt(public_key, number):
    encrypted_number = public_key.encrypt(number)
    return encrypted_number


# Desciframos utilizando la clave privada
def decrypt(private_key, encrypted_number):
    decrypted_number = private_key.decrypt(encrypted_number)
    return decrypted_number


# El cálculo de la intersección usando los sets de dos nodos.
# Nodo 1 solicita -> Nodo 2 calcula. Se implementará una forma de que le envíe la intersección de vuelta.
def calculate_intersection(node1_encrypted_set, node2_encrypted_set, public_key):
    # Convertir los conjuntos de números cifrados en conjuntos de EncryptedNumber para poder calcular la intersección
    node1_enc_set = {paillier.EncryptedNumber(public_key, int(num['ciphertext']), int(num['exponent']))
                     for num in node1_encrypted_set}
    node2_enc_set = {paillier.EncryptedNumber(public_key, int(num['ciphertext']), int(num['exponent']))
                     for num in node2_encrypted_set}

    # Calcular la intersección de los conjuntos
    intersection = node1_enc_set.intersection(node2_enc_set)

    # Convertir la intersección en una lista de diccionarios para su serialización
    intersection_serialized = [{'ciphertext': str(num.ciphertext()), 'exponent': num.exponent}
                               for num in intersection]

    return intersection_serialized

