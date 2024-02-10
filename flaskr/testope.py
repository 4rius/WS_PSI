""" Paillier PSI usando Evaluación polinómica - PoC """

import phe.paillier as paillier
import random

# === Alice's Setup ===
public_key, private_key = paillier.generate_paillier_keypair()


def calcular_coeficientes(raices):
    coeficientes = [1]

    for raiz in raices:
        nuevos_coeficientes = [0] * (len(coeficientes) + 1)
        for i in range(len(coeficientes)):
            nuevos_coeficientes[i] += coeficientes[i]
            nuevos_coeficientes[i + 1] -= raiz * coeficientes[i]
        coeficientes = nuevos_coeficientes

    return coeficientes


# (x - 1)(x - 2)(x - 3)(x - 4)(x - 5)
alice_set = [1, 2, 3, 4, 5]

# Calcular los coeficientes del polinomio
coeficientes = calcular_coeficientes(alice_set)

# Imprimir los coeficientes
print("Coeficientes:", coeficientes)

# Ciframos los coeficientes y se los "mandamos" a Bob
encrypted_coefficients = [public_key.encrypt(coef) for coef in coeficientes]

# === Bob's Setup ===
bob_set = [3, 4, 5, 6, 7]


# Evaluación de un polinomio usando el método de Horner
def horner_eval(coefs, x):
    result = coefs[-1]
    for coef in reversed(coefs[:-1]):
        result = result * x + coef
    return result


# Para cada elemento en el set de Bob, calculamos un valor aleatorio r y usamos la propiedad de homomorfismo de
# Paillier para evaluar el polinomio cifrado en ese punto
encrypted_result = []
for element in bob_set:
    rb = random.randint(1, 1000)
    Epbj = horner_eval(encrypted_coefficients, element)
    encrypted_result.append(paillier.EncryptedNumber(public_key, Epbj.ciphertext(be_secure=False) * rb + element))

# (Bob manda de vuelta los resultados, donde haya un 0 es que el elemento de Bob está en
# el set de Alice, representan la intersección)
result = [private_key.decrypt(result) for result in encrypted_result]
print("Resultado:", result)
intersection = [bob_set[i] for i, val in enumerate(result) if val == 0]
print("Intersección:", intersection)
