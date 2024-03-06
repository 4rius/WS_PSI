import time

from flaskr import Logs
from flaskr.DbConstants import VERSION
from flaskr.Logs import ThreadData
from flaskr.implementations.Polynomials import polinomio_raices


class IntersectionHandler:
    def __init__(self, my_data, devices, results, id, domain):
        self.my_data = my_data
        self.devices = devices
        self.results = results
        self.id = id
        self.domain = domain

    def intersection_first_step_ope(self, device, cs):
        """
        This method performs the first step of the intersection operation using Oblivious Polynomial Evaluation (OPE)

        Parameters:
        device (str): The device with which the intersection operation is being performed.
        cs (Cryptosystem): The cryptosystem being used for the operation.

        The method follows these steps:
        1. Starts logging the operation.
        2. Serializes the public key of the cryptosystem.
        3. Converts the data to integers and adds them to a list.
        4. Calculates the roots of the polynomial that has the data as coefficients.
        5. Encrypts the coefficients.
        6. Gets the ciphertext of the encrypted coefficients.
        7. Prints the coefficients being sent.
        8. Sends the coefficients to the device.
        9. Stops logging the operation.
        10. Logs the activity.
        """
        start_time = time.time()
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        serialized_pubkey = cs.serialize_public_key()
        my_data = [int(element) for element in self.my_data]
        coeffs = polinomio_raices(my_data)
        encrypted_coeffs = [cs.encrypt(coeff) for coeff in coeffs]
        encrypted_coeffs = [cs.get_ciphertext(encrypted_coeff) for encrypted_coeff in encrypted_coeffs]
        print(f"Intersection with {device} - {cs.__class__.__name__}_OPE - Sending coeffs: {encrypted_coeffs}")
        message = {'data': encrypted_coeffs, 'implementation': (cs.__class__.__name__ + ' OPE'), 'peer': self.id,
                   'pubkey': serialized_pubkey}
        self.devices[device]["socket"].send_json(message)
        end_time = time.time()
        Logs.stop_logging(thread_data)
        Logs.log_activity(thread_data, "INTERSECTION_" + cs.__class__.__name__ + "_OPE_1", end_time - start_time, VERSION,
                          self.id,
                          device)

    def handle_ope(self, peer_data, coeffs, pubkey, cs):
        """
        This method handles the Oblivious Polynomial Evaluation (OPE) operation for the device that receives the coefficients.

        Parameters:
        peer_data (dict): The data received from the peer device.
        coeffs (list): The coefficients of the polynomial.
        pubkey (str): The public key of the cryptosystem.
        cs (Cryptosystem): The cryptosystem being used for the operation.

        Returns:
        tuple: A tuple containing the peer data, the evaluated coefficients, and the name of the cryptosystem operation.
        """
        my_data = [int(element) for element in self.my_data]
        pubkey = cs.reconstruct_public_key(pubkey)
        coeffs = cs.get_encrypted_list(coeffs, pubkey)
        encrypted_evaluated_coeffs = cs.eval_coefficients(coeffs, pubkey, my_data)
        return peer_data, encrypted_evaluated_coeffs, (cs.__class__.__name__ + " OPE")

    def intersection_final_step_ope(self, peer_data, cs):
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
        start_time = time.time()
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        result = cs.get_encrypted_list_f(peer_data['data'])
        result = [int(cs.decrypt(encrypted_value)) for encrypted_value in result]
        print(f"Intersection with {peer_data['peer']} - {cs.__class__.__name__} OPE - Raw results: {result}")
        device = peer_data['peer']
        result_formatted = [element for element in result if element in self.my_data]
        self.results[device] = result_formatted
        end_time = time.time()
        Logs.stop_logging(thread_data)
        Logs.log_activity(thread_data, "INTERSECTION_" + cs.__class__.__name__ + "_OPE_F", end_time - start_time, VERSION,
                          self.id,
                          device)
        Logs.log_result("INTERSECTION_" + (cs.__class__.__name__ + '_OPE'), result_formatted, VERSION, self.id, device)
        print(f"Intersection with {device} - {cs.__class__.__name__} OPE - Result: {result_formatted}")

    def intersection_first_step(self, device, cs):
        start_time = time.time()
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        encrypted_data = cs.encrypt_my_data(self.my_data, self.domain)
        serialized_pubkey = cs.serialize_public_key()
        encrypted_data = {element: cs.get_ciphertext(encrypted_value) for element, encrypted_value in encrypted_data.items()}
        print(f"Intersection with {device} - {cs.__class__.__name__} - Sending data: {encrypted_data}")
        message = {'data': encrypted_data, 'implementation': cs.__class__.__name__, 'peer': self.id,
                   'pubkey': serialized_pubkey}
        self.devices[device]["socket"].send_json(message)
        end_time = time.time()
        Logs.stop_logging(thread_data)
        Logs.log_activity(thread_data, "INTERSECTION_" + cs.__class__.__name__ + "_1", end_time - start_time, VERSION,
                          self.id,
                          device)

    def handle_intersection(self, peer_data, cs, pubkey):
        pubkey = cs.reconstruct_public_key(pubkey)
        multiplied_set = cs.get_multiplied_set(cs.get_encrypted_set(peer_data['data'], pubkey), self.my_data)
        return peer_data, multiplied_set, cs.__class__.__name__

    def intersection_final_step(self, peer_data, cs):
        start_time = time.time()
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        multiplied_set = cs.recv_multiplied_set(peer_data['data'], cs.public_key)
        device = peer_data['peer']
        for element, encrypted_value in multiplied_set.items():
            multiplied_set[element] = cs.decrypt(encrypted_value)
        multiplied_set = {element for element, value in multiplied_set.items() if value == 1}
        self.results[device] = multiplied_set
        end_time = time.time()
        Logs.stop_logging(thread_data)
        Logs.log_activity(thread_data, "INTERSECTION_" + cs.__class__.__name__ + "_F", end_time - start_time, VERSION,
                          self.id,
                          device)
        # Make multiplied_set serializable
        multiplied_set = list(multiplied_set)
        Logs.log_result("INTERSECTION_" + cs.__class__.__name__, multiplied_set, VERSION, self.id, device)
        print(f"Intersection with {device} - {cs.__class__.__name__} - Result: {multiplied_set}")
