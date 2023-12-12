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
    # TODO: Implementar el cálculo de la intersección usando el esquema PSI y viendo cómo lidiar con el probabilismo
    #       de Paillier
    return []

