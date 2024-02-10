import phe.paillier as paillier

# Alice
public_key, private_key = paillier.generate_paillier_keypair()
alice_set = [1, 2, 3, 4, 5]
encrypted_alice_set = [public_key.encrypt(x) for x in alice_set]

# Bob
bob_set = [3, 4, 5, 6, 7]
encrypted_results = []

for element in bob_set:
    encrypted_element = public_key.encrypt(element)
    for encrypted_alice_item in encrypted_alice_set:
        result = encrypted_alice_item - encrypted_element
        encrypted_results.append(result)

# Último paso: Bob manda de vuelta los resultados, donde haya un 0 es que el elemento de Bob está en el set de Alice, representan la intersección
results = [private_key.decrypt(result) for result in encrypted_results]

# Buscar los índices de los elementos de Bob que están en el set de Alice
intersection = [bob_set[i//len(alice_set)] for i, val in enumerate(results) if val == 0]  # i//len(alice_set) es el índice del elemento de Bob
print("Intersection:", intersection)

