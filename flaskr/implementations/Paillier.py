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
    intersection = []
    # Recorre cada número encriptado en el primer conjunto
    for encrypted_number1 in node1_encrypted_set:
        # Compara ese número con cada número encriptado en el segundo conjunto
        for encrypted_number2 in node2_encrypted_set:
            # Deserializa los números encriptados
            enc_num1 = paillier.EncryptedNumber(private_key.public_key(), int(encrypted_number1['ciphertext']),
                                                int(encrypted_number1['exponent']))
            enc_num2 = paillier.EncryptedNumber(private_key.public_key(), int(encrypted_number2['ciphertext']),
                                                int(encrypted_number2['exponent']))
            if enc_num1 == enc_num2:
                # Desencripta el número y lo agrega a la lista de intersección
                intersection.append(private_key.decrypt(enc_num1))
    # Devuelve la lista de intersección
    return intersection
