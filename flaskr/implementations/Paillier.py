from phe import paillier, EncryptedNumber


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


def get_encrypted_set(serialized_encrypted_set, public_key):
    return {element: EncryptedNumber(public_key, int(ciphertext)) for element, ciphertext in
            serialized_encrypted_set.items()}


# Cifrar los números de los sets con los que arrancamos
def encrypt(public_key, number):
    encrypted_number = public_key.encrypt(number)
    return encrypted_number


# Desciframos utilizando la clave privada
def decrypt(private_key, encrypted_number):
    decrypted_number = private_key.decrypt(encrypted_number)
    return decrypted_number


def encrypt_my_data(my_set, public_key, domain):
    # Propósito de depuración
    print("Ciframos los elementos del set A")
    result = {}
    for element in range(domain):
        if element not in my_set:
            print("Elemento no encontrado en el set: " + str(element))
            result[element] = public_key.encrypt(0)
        else:
            print("Elemento encontrado en el set: " + str(element))
            result[element] = public_key.encrypt(1)
    return result
    # return {element: public_key.encrypt(1) if element in my_set else public_key.encrypt(0) for element in range(domain)}


def recv_multiplied_set(serialized_multiplied_set, public_key):
    return {element: EncryptedNumber(public_key, int(ciphertext)) for element, ciphertext in
            serialized_multiplied_set.items()}


def get_multiplied_set(enc_set, node_set):
    # Cita: https://blog.openmined.org/private-set-intersection-with-the-paillier-cryptosystem/
    # Propósito de depuración
    print("Multiplicamos por 0 o por 1 los elementos del set A dependiendo de si están en el set B")
    result = {}
    for element, encrypted_value in enc_set.items():
        if int(element) not in node_set:
            print("Elemento no encontrado en el set: " + str(element))
            result[element] = encrypted_value * 0
        else:
            print("Elemento encontrado en el set: " + str(element))
            result[element] = encrypted_value * 1
    return result
    # return {element: encrypted_value * int(element in node_set) for element, encrypted_value in enc_set.items()}
