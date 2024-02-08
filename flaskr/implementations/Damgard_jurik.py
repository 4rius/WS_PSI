from damgard_jurik import keygen, EncryptedNumber, PublicKey


def generate_keypair_dj():
    public_key, private_key_ring = keygen(n_bits=1024, s=2, threshold=1, n_shares=1)
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
    return PublicKey(int(public_key_dict['n']), int(public_key_dict['s']), int(public_key_dict['m']),
                     int(public_key_dict['threshold']), int(public_key_dict['delta']))


def get_encrypted_set_dj(serialized_encrypted_set, public_key):
    return {element: EncryptedNumber(ciphertext, public_key) for element, ciphertext in
            serialized_encrypted_set.items()}


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
        # Convertir el valor encriptado a un entero antes de multiplicarlo
        result[element] = EncryptedNumber(public_key=encrypted_value.public_key,
                                          value=int(encrypted_value.value)) * multiplier
    return result


def intersection_enc_size_dj(multiplied_set):
    return sum([int(element.value) for element in multiplied_set.values()])
