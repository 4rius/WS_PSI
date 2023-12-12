from collections import defaultdict

from phe import paillier


# Devuelve los objetos clave pública y privada
def generate_keys():
    public_key, private_key = paillier.generate_paillier_keypair()
    return public_key, private_key


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
def calculate_intersection(node1_encrypted_set, node2_encrypted_set, private_key):
    # Diccionario para almacenar los números encriptados del primer conjunto
    encrypted_set_dict = defaultdict(list)
    for encrypted_number in node1_encrypted_set:
        enc_num = paillier.EncryptedNumber(private_key.public_key, int(encrypted_number['ciphertext']),
                                           int(encrypted_number['exponent']))
        # Almacena el número encriptado en el diccionario usando su hash como clave
        encrypted_set_dict[hash(enc_num)].append(enc_num)

    intersection = []
    # Recorre cada número encriptado en el segundo conjunto
    for encrypted_number in node2_encrypted_set:
        enc_num = paillier.EncryptedNumber(private_key.public_key, int(encrypted_number['ciphertext']),
                                           int(encrypted_number['exponent']))
        # Verifica si el hash del número encriptado existe en el diccionario
        if hash(enc_num) in encrypted_set_dict:
            # Desencripta el número y lo agrega a la lista de intersección
            intersection.append(private_key.decrypt(enc_num))

    return intersection

