from Network import Logs
from Network.helpers.IntersectionHelper import IntersectionHelper
from Network.helpers.DbConstants import VERSION
from Network.helpers.Polynomials import polinomio_raices
from Network.helpers.log_activity import log_activity


class OPEHandler(IntersectionHelper):
    def __init__(self, id, my_data, domain, devices, results):
        super().__init__(id, my_data, domain, devices, results)

    @log_activity
    def intersection_first_step(self, device, cs):
        """
        This method performs the first step of the intersection operation using Oblivious Polynomial Evaluation (OPE)

        Parameters:
        device (str): The device with which the intersection operation is being performed.
        cs (Cryptosystem): The cryptosystem being used for the operation.

        The method follows these steps:
        1. Serializes the public key of the cryptosystem.
        2. Converts the data to integers and adds them to a list.
        3. Calculates the roots of the polynomial that has the data as coefficients.
        4. Encrypts the coefficients.
        5. Gets the ciphertext of the encrypted coefficients.
        6. Prints the coefficients being sent.
        7. Sends the coefficients to the device.
        """
        serialized_pubkey = cs.serialize_public_key()
        my_data = [int(element) for element in self.my_data]
        coeffs = polinomio_raices(my_data)
        encrypted_coeffs = [cs.encrypt(coeff) for coeff in coeffs]
        encrypted_coeffs = [cs.get_ciphertext(encrypted_coeff) for encrypted_coeff in encrypted_coeffs]
        print(f"Intersection with {device} - {cs.imp_name}_OPE - Sending coeffs: {encrypted_coeffs}")
        if type == "PSI-CA":
            self.send_message(device, encrypted_coeffs, (cs.imp_name + ' PSI-CA OPE'), serialized_pubkey)
        else:
            self.send_message(device, encrypted_coeffs, (cs.imp_name + ' OPE'), serialized_pubkey)

    @log_activity
    def intersection_second_step(self, device, cs, coeffs, pubkey):
        """
        This method handles the Oblivious Polynomial Evaluation (OPE) operation for the device that receives
        the coefficients

        Parameters:
        peer_data (dict): The data received from the peer device.
        coeffs (list): The coefficients of the polynomial.
        pubkey (str): The public key of the cryptosystem.
        cs (Cryptosystem): The cryptosystem being used for the operation.
        device (str): The device with which the intersection operation is being performed. Used for logging.

        Returns:
        tuple: A tuple containing the peer data, the evaluated coefficients, and the name of the cryptosystem operation.
        """
        my_data = [int(element) for element in self.my_data]
        pubkey = cs.reconstruct_public_key(pubkey)
        coeffs = cs.get_encrypted_list(coeffs, pubkey)
        encrypted_evaluated_coeffs = cs.eval_coefficients(coeffs, pubkey, my_data)
        serialized_encrypted_evaluated_coeffs = cs.serialize_result(encrypted_evaluated_coeffs, "OPE")
        self.send_message(device, serialized_encrypted_evaluated_coeffs, cs.imp_name + ' OPE')

    @log_activity
    def intersection_final_step(self, device, cs, peer_data):
        """
        This method performs the final step of the intersection operation using Oblivious Polynomial Evaluation (OPE).

        Parameters:
        peer_data (dict): The data received from the peer device we started the operation with.
        cs (Cryptosystem): The cryptosystem being used for the operation.

        The method follows these steps:
        1. Starts logging the operation.
        2. Gets the encrypted list from the peer data.
        3. Decrypts the encrypted values and converts them to integers.
        4. Prints the raw results of the operation.
        5. Formats the results by filtering out elements not in the original data.
        6. Stores the formatted results.
        7. Stops logging the operation.
        8. Logs the activity.
        9. Logs the result.
        10. Prints the final result of the operation.
        """
        result = cs.get_encrypted_list_f(peer_data)
        result = [int(cs.decrypt(encrypted_value)) for encrypted_value in result]
        print(f"Intersection with {device} - {cs.imp_name} OPE - Raw results: {result}")
        result_formatted = [element for element in result if element in self.my_data]
        self.results[device] = result_formatted
        Logs.log_result(cs.imp_name + '_OPE', result_formatted, VERSION, self.id, device)
        print(f"Intersection with {device} - {cs.imp_name} OPE - Result: {result_formatted}")
