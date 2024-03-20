def polinomio_raices(roots, neg_one=-1, one=1):
    """
    Interpolates the unique polynomial that encodes the given roots.
    The function also requires the one and the negative one of the underlying ring.
    """
    print("Calculo de polinomio con raices: " + str(roots))
    zero = one + neg_one
    coefs = [neg_one * roots[0], one]
    for r in roots[1:]:
        coefs = multiplicar_polinomios(coefs, [neg_one * r, one], zero)
    print("Coeficientes del polinomio: " + str(coefs))
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
