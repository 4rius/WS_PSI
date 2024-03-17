""" Paillier PSI usando Evaluación polinómica - PoC """

import phe.paillier as paillier
import random

# === Alice's Setup ===
public_key, private_key = paillier.generate_paillier_keypair()


def poly_from_roots(roots, neg_one, one):
    """
    Interpolates the unique polynomial that encodes the given roots.
    The function also requires the one and the negative one of the underlying ring.
    """
    zero = one + neg_one
    coefs = [neg_one * roots[0], one]
    for r in roots[1:]:
        coefs = poly_mul(coefs, [neg_one * r, one], zero)
    return coefs


def poly_mul(coefs1, coefs2, zero):
    """
    Multiplies two polynomials whose coefficients are given in coefs1 and coefs2.
    Zero value of the underlying ring is required on the input zero.
    """
    coefs3 = [zero] * (len(coefs1) + len(coefs2) - 1)
    for i in range(len(coefs1)):
        for j in range(len(coefs2)):
            coefs3[i + j] += coefs1[i] * coefs2[j]
    return coefs3


alice_set = [1, 2, 3, 4, 5, 7, 8]

# Generamos un polinomio que tenga como raíces los elementos de alice_set
coeficientes = poly_from_roots(alice_set, -1, 1)

# Imprimir los coeficientes
print("Coeficientes:", coeficientes)


# Evaluación de un polinomio cifrado usando el método de Horner
def horner_eval_crypt(coefs, x):
    result = coefs[-1]
    for coef in reversed(coefs[:-1]):
        result = coef._add_encrypted(x * result)
    return result


# Ciframos los coeficientes y se los "mandamos" a Bob
encrypted_coeff = [public_key.encrypt(coef) for coef in coeficientes]

# === Bob's Setup ===
bob_set = [2, 3, 6, 8, 1, 9]
Eval = encrypted_coeff[0]._add_encrypted(encrypted_coeff[1] * 2)
print(private_key.decrypt(Eval))

# Para cada elemento en el set de Bob, calculamos un valor aleatorio r y usamos la propiedad de homomorfismo de
# Paillier para evaluar el polinomio cifrado en ese punto
encrypted_result = []
for element in bob_set:
    rb = random.randint(1, 1000)
    Epbj = horner_eval_crypt(encrypted_coeff, element)
    encrypted_result.append(public_key.encrypt(element)._add_encrypted(rb * Epbj))

# Resultados
result = [private_key.decrypt(result) for result in encrypted_result]
print("Resultado:", result)
intersection = []
for element in result:
    if element in alice_set:
        intersection.append(element)
print("Intersección:", intersection)
