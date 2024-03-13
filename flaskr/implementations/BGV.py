import random

from flaskr.implementations.PyFHE.CRTPoly import CRTPoly
from flaskr.implementations.PyFHE.FHE import FHE
from flaskr.implementations.CryptoSystem import CryptoSystem
from flaskr.implementations.PyFHE.numTh import findPrimes
import json

# Uses PyFHE: https://github.com/Jyun-Neng/PyFHE
class BGV(CryptoSystem):

    def __init__(self):
        poly_degree = 4096
        stdev = 3.2
        L = 4
        primes, bits = findPrimes(22, 4096, 4)
        a, bits = findPrimes(10, 4096, 1)
        P = a[0]
        modulus = 1
        for prime in primes:
            modulus *= prime
        self.f = FHE(poly_degree, stdev, primes, P, L)
        self.sk, self.pk, self.switch_keys = self.generate_keys()

    def encrypt(self, plaintext):
        return self.f.homoEnc(plaintext, self.pk)

    def decrypt(self, ciphertext):
        return self.f.homoDec(ciphertext, self.sk)

    def generate_keys(self):
        self.sk = self.f.secretKeyGen(64)
        self.pk = self.f.publicKeyGen(self.sk)
        self.switch_keys = self.f.switchKeyGen(self.sk)
        return self.sk, self.pk, self.switch_keys

    def serialize_public_key(self):
        """
        Serializa la clave pública en un diccionario con el módulo y el conjunto de primos
        """
        public_key_dict = {
            'b': str(self.pk[0]),
            'neg_A': str(self.pk[1])
        }
        return public_key_dict

    def reconstruct_public_key(self, public_key_dict):
        """
        Reconstruye la clave pública a partir del diccionario
        """
        return [int(public_key_dict['b']), [int(x) for x in public_key_dict['neg_A']]]

    import random

    def horner_encrypted_eval_bgv(self, coefs, x, primes):
        result = coefs[-1]
        for coef in reversed(coefs[:-1]):
            # Use homomorphic addition and multiplication
            result = self.homoAdd(coef, self.homoMultiply(x, result, primes), primes)
        return result

    def eval_coefficients(self, coefs, my_data, primes):
        print("Evaluamos el polinomio en los elementos del set B")
        encrypted_results = []
        for element in my_data:
            rb = random.randint(1, 1000)
            Epbj = self.horner_encrypted_eval_bgv(coefs, self.encrypt(element), primes)
            # Use homomorphic addition and multiplication
            encrypted_results.append(self.homoAdd(self.encrypt(element), self.homoMultiply(rb, Epbj, primes), primes))
        return encrypted_results

    def compute_results(self, recv_evaluation_set):
        decrypted_set = [self.decrypt(element) for element in recv_evaluation_set]
        intersection = []
        return intersection

    def homoMultiply(self, c1, c2, primes):
        result = []
        fft_c10 = CRTPoly(c1[0], primes)
        fft_c11 = CRTPoly(c1[1], primes)
        fft_c20 = CRTPoly(c2[0], primes)
        fft_c21 = CRTPoly(c2[1], primes)
        fft_result0 = fft_c10 * fft_c20
        fft_result1 = fft_c10 * fft_c21 + fft_c11 * fft_c20
        fft_result2 = fft_c11 * fft_c21
        result.append(fft_result0.toPoly())
        result.append(fft_result1.toPoly())
        result.append(fft_result2.toPoly())
        return result

    def homoAdd(self, c1, c2, primes):
        result = []
        fft_c10 = CRTPoly(c1[0], primes)
        fft_c11 = CRTPoly(c1[1], primes)
        fft_c20 = CRTPoly(c2[0], primes)
        fft_c21 = CRTPoly(c2[1], primes)
        fft_result0 = fft_c10 + fft_c20
        fft_result1 = fft_c11 + fft_c21
        result.append(fft_result0.toPoly())
        result.append(fft_result1.toPoly())
        return result


