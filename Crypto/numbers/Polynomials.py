from Network.collections.DbConstants import DEFL_DOMAIN
from util.polynomial import Polynomial


def polinomio_raices(roots, neg_one=-1, one=1, cs=None):
    """
    Interpolates the unique polynomial that encodes the given roots.
    The function also requires the one and the negative one of the underlying ring.
    """
    print("Calculo de polinomio con raices: " + str(roots))
    if cs is not None and cs == "BFV":
        return polinomio_raices_bfv(roots)
    zero = one + neg_one
    coefs = [neg_one * roots[0], one]
    for r in roots[1:]:
        coefs = multiplicar_polinomios(coefs, [neg_one * r, one], zero)
    # print("Coeficientes del polinomio: " + str(coefs))
    return coefs


def multiplicar_polinomios(coefs1, coefs2, zero=0):
    """
    Multiplies two polynomials whose coefficients are given in coefs1 and coefs2.
    Zero value of the underlying ring is required on the input zero.
    """
    coefs3 = [zero] * (len(coefs1) + len(coefs2) - 1)
    for i in range(len(coefs1)):
        for j in range(len(coefs2)):
            coefs3[i + j] += coefs1[i] * coefs2[j]
    return coefs3


# Método específico para esta librería por su manejo concreto de polinomios
def polinomio_raices_bfv(roots):
    grado = len(roots) + 1
    result = Polynomial(grado, [-roots[0], 1] + [0] * (grado - 2))
    for r in roots[1:]:
        result = Polynomial(grado, [-r, 1] + [0] * (grado - 2)).multiply(result, DEFL_DOMAIN)
    return result.coeffs
