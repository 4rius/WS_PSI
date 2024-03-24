import time

from flaskr import Logs
from flaskr.Logs import ThreadData
from flaskr.helpers.DbConstants import VERSION
from flaskr.helpers.Polynomials import polinomio_raices


def log_activity(func):
    def wrapper(self, *args, **kwargs):
        start_time = time.time()  # Tiempo de inicio
        thread_data = ThreadData()
        Logs.start_logging(thread_data)
        result = func(self, *args, **kwargs)  # Ejecución de la función
        end_time = time.time()  # Tiempo de finalización
        Logs.stop_logging(thread_data)
        device = args[0] if len(args) > 0 else None
        cs = args[1] if len(args) > 1 else None
        activity_code = func.__name__.upper() + ("_" + cs.imp_name if cs is not None else "")
        Logs.log_activity(thread_data, activity_code, end_time - start_time, VERSION, self.id, device)
        return result

    return wrapper


class IntersectionHandler:
    def __init__(self, id, my_data, domain, devices, results):
        # Añadimos las variables de instancia de la clase Node para facilitar el acceso a los datos
        self.id = id
        self.my_data = my_data
        self.domain = domain
        self.devices = devices
        self.results = results

    @log_activity
    def intersection_first_step_ope(self, device, cs, type="PSI"):
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
    def intersection_second_step_ope(self, device, cs, coeffs, pubkey):
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
    def intersection_final_step_ope(self, device, cs, peer_data):
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
        print(f"Intersection with {device} - {cs.imp_name} OPE - Result: {result_formatted}")

    @log_activity
    def intersection_first_step(self, device, cs):
        encrypted_data = cs.encrypt_my_data(self.my_data, self.domain)
        serialized_pubkey = cs.serialize_public_key()
        encrypted_data = {element: cs.get_ciphertext(encrypted_value) for element, encrypted_value in
                          encrypted_data.items()}
        print(f"Intersection with {device} - {cs.imp_name} - Sending data: {encrypted_data}")
        self.send_message(device, encrypted_data, cs.imp_name, serialized_pubkey)

    @log_activity
    def intersection_second_step(self, device, cs, peer_data, pubkey):
        pubkey = cs.reconstruct_public_key(pubkey)
        multiplied_set = cs.get_multiplied_set(cs.get_encrypted_set(peer_data, pubkey), self.my_data)
        serialized_multiplied_set = cs.serialize_result(multiplied_set)
        self.send_message(device, serialized_multiplied_set, cs.imp_name)

    @log_activity
    def intersection_final_step(self, device, cs, peer_data):
        multiplied_set = cs.recv_multiplied_set(peer_data, cs.public_key)
        for element, encrypted_value in multiplied_set.items():
            multiplied_set[element] = cs.decrypt(encrypted_value)
        multiplied_set = {element for element, value in multiplied_set.items() if value == 1}
        # Make multiplied_set serializable
        multiplied_set = list(multiplied_set)
        self.results[device] = multiplied_set
        Logs.log_result("INTERSECTION_" + cs.imp_name, multiplied_set, VERSION, self.id, device)
        print(f"Intersection with {device} - {cs.imp_name} - Result: {multiplied_set}")

    @log_activity
    def intersection_second_step_psi_ca_ope(self, device, cs, coeffs, pubkey):
        my_data = [int(element) for element in self.my_data]
        pubkey = cs.reconstruct_public_key(pubkey)
        coeffs = cs.get_encrypted_list(coeffs, pubkey)
        result = cs.get_evaluations(coeffs, pubkey, my_data)
        serialized_result = cs.serialize_result(result, "OPE")
        self.send_message(device, serialized_result, cs.imp_name + ' PSI-CA OPE')

    @log_activity
    def final_step_psi_ca_ope(self, device, cs, peer_data):
        result = cs.get_encrypted_list_f(peer_data)
        result = [int(cs.decrypt(encrypted_value)) for encrypted_value in result]
        print(f"Intersection with {device} - {cs.imp_name} PSI-CA OPE - Raw results: {result}")
        # When the element is 0, it means it's in the intersection
        cardinality = sum([int(element == 0) for element in result])
        self.results[device] = cardinality
        Logs.log_result((cs.imp_name + '_PSI-CA_OPE'), cardinality, VERSION, self.id, device)
        print(f"Cardinality calculation with {device} - {cs.imp_name} PSI-CA OPE - Result: {cardinality}")

    def send_message(self, peer, ser_enc_res, implementation, peer_pubkey=None):
        if peer_pubkey:
            message = {'data': ser_enc_res, 'implementation': implementation, 'peer': self.id,
                       'pubkey': peer_pubkey, 'step': '2'}
        else:
            message = {'data': ser_enc_res, 'implementation': implementation, 'peer': self.id, 'step': 'F'}
        self.devices[peer]["socket"].send_json(message)
