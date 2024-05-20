import random

from bfv.batch_encoder import BatchEncoder
from bfv.bfv_decryptor import BFVDecryptor
from bfv.bfv_encryptor import BFVEncryptor
from bfv.bfv_evaluator import BFVEvaluator
from bfv.bfv_key_generator import BFVKeyGenerator
from bfv.bfv_parameters import BFVParameters
from util.polynomial import Polynomial

plain_modulus = 89

elementos_A = [2, 1, 4, 7, 9]  # tienen que ser menor que plain_modulus

elementos_B = [1, 4, 5, 6, 9]  # tienen que ser menor que plain_modulus


def poly_from_roots(roots):
    grado = len(roots) + 1

    result = Polynomial(grado, [-roots[0], 1] + [0] * (grado - 2))

    for r in roots[1:]:
        result = Polynomial(grado, [-r, 1] + [0] * (grado - 2)).multiply(result, plain_modulus)

    return result.coeffs


def naive_eval_crypt(encripted_coeff, x, relin_key, evaluator, encoder, encryptor):
    result = encripted_coeff[0]

    for pos, coef in enumerate(encripted_coeff[1:]):
        encrypt_x = encryptor.encrypt(encoder.encode([x ** (pos + 1), 0]))

        termino = evaluator.multiply(encrypt_x, coef, relin_key)

        result = evaluator.add(result, termino)

    rb = random.randint(1, 10)

    temp = evaluator.multiply(encryptor.encrypt(encoder.encode([rb, 0])), result, relin_key)

    return evaluator.add(temp, encryptor.encrypt(encoder.encode([x, 0])))


def main():
    degree = 2

    ciph_modulus = 8000000000000

    params = BFVParameters(poly_degree=degree,

                           plain_modulus=plain_modulus,

                           ciph_modulus=ciph_modulus)

    key_generator = BFVKeyGenerator(params)

    public_key = key_generator.public_key

    secret_key = key_generator.secret_key

    relin_key = key_generator.relin_key

    encoder = BatchEncoder(params)

    encryptor = BFVEncryptor(params, public_key)

    decryptor = BFVDecryptor(params, secret_key)

    evaluator = BFVEvaluator(params)

    coeficientes = poly_from_roots(elementos_A)  # Lista

    encripted_coeff = []

    for coeff in coeficientes:
        ciph1 = encryptor.encrypt(encoder.encode([coeff, 0]))

        encripted_coeff.append(ciph1)

    # Alice manda a bob los coficientes encriptados

    resultado_encripted = []

    for elemento in elementos_B:
        temp = naive_eval_crypt(encripted_coeff,
                                elemento,
                                relin_key,
                                evaluator,
                                encoder,
                                encryptor)

        temp = decryptor.decrypt(temp)

        temp = encoder.decode(temp)

        resultado_encripted.append(temp)

    resultado_decoded = [a[0] for a in resultado_encripted]
    print("Resultado: ", resultado_decoded)
    intersection = []
    for i in elementos_A:
        if i in resultado_decoded:
            intersection.append(i)

    return intersection


# Ebi-< Hornel_eval( Ebj)) ->


if __name__ == '__main__':
    for i in range(100):
        res = main()
        # Intersección real
        print("Intersección real: ", [a for a in elementos_A if a in elementos_B])
        if res != [a for a in elementos_A if a in elementos_B]:
            print("Intersección incorrecta en la iteración: ", i)
        print("Intersection: " + str(main()))
        print("#####################")