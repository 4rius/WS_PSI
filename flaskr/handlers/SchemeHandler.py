import concurrent.futures
import threading
import time

from flaskr import Logs
from flaskr.DbConstants import VERSION, TEST_ROUNDS
from flaskr.Logs import ThreadData
from flaskr.implementations.Damgard_jurik import DamgardJurik
from flaskr.implementations.Paillier import Paillier
from flaskr.implementations.Polynomials import polinomio_raices


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
        activity_code = func.__name__.upper() + ("_" + cs.__class__.__name__.upper() if cs is not None else "")
        Logs.log_activity(thread_data, activity_code, end_time - start_time, VERSION, self.id, device)
        return result

    return wrapper


class SchemeHandler:
    def __init__(self, my_data, devices, results, id, domain):
        self.my_data = my_data
        self.devices = devices
        self.results = results
        self.id = id
        self.domain = domain
        self.paillier = Paillier()
        self.damgard_jurik = DamgardJurik()

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
        print(f"Intersection with {device} - {cs.__class__.__name__}_OPE - Sending coeffs: {encrypted_coeffs}")
        if type == "PSI-CA":
            message = {'data': encrypted_coeffs, 'implementation': (cs.__class__.__name__ + ' PSI-CA OPE'),
                       'peer': self.id,
                       'pubkey': serialized_pubkey}
        else:
            message = {'data': encrypted_coeffs, 'implementation': (cs.__class__.__name__ + ' OPE'), 'peer': self.id,
                       'pubkey': serialized_pubkey}
        self.devices[device]["socket"].send_json(message)

    @log_activity
    def handle_ope(self, device, cs, peer_data, coeffs, pubkey):
        """
        This method handles the Oblivious Polynomial Evaluation (OPE) operation for the device that receives the coefficients.

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
        return peer_data, encrypted_evaluated_coeffs, (cs.__class__.__name__ + " OPE")

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
        result = cs.get_encrypted_list_f(peer_data['data'])
        result = [int(cs.decrypt(encrypted_value)) for encrypted_value in result]
        print(f"Intersection with {peer_data['peer']} - {cs.__class__.__name__} OPE - Raw results: {result}")
        result_formatted = [element for element in result if element in self.my_data]
        self.results[device] = result_formatted
        print(f"Intersection with {device} - {cs.__class__.__name__} OPE - Result: {result_formatted}")

    @log_activity
    def intersection_first_step(self, device, cs):
        encrypted_data = cs.encrypt_my_data(self.my_data, self.domain)
        serialized_pubkey = cs.serialize_public_key()
        encrypted_data = {element: cs.get_ciphertext(encrypted_value) for element, encrypted_value in
                          encrypted_data.items()}
        print(f"Intersection with {device} - {cs.__class__.__name__} - Sending data: {encrypted_data}")
        message = {'data': encrypted_data, 'implementation': cs.__class__.__name__, 'peer': self.id,
                   'pubkey': serialized_pubkey}
        self.devices[device]["socket"].send_json(message)

    @log_activity
    def handle_intersection(self, device, cs, peer_data, pubkey):
        pubkey = cs.reconstruct_public_key(pubkey)
        multiplied_set = cs.get_multiplied_set(cs.get_encrypted_set(peer_data['data'], pubkey), self.my_data)
        return peer_data, multiplied_set, cs.__class__.__name__

    @log_activity
    def intersection_final_step(self, device, cs, peer_data):
        multiplied_set = cs.recv_multiplied_set(peer_data['data'], cs.public_key)
        for element, encrypted_value in multiplied_set.items():
            multiplied_set[element] = cs.decrypt(encrypted_value)
        multiplied_set = {element for element, value in multiplied_set.items() if value == 1}
        self.results[device] = multiplied_set
        end_time = time.time()
        # Make multiplied_set serializable
        multiplied_set = list(multiplied_set)
        Logs.log_result("INTERSECTION_" + cs.__class__.__name__, multiplied_set, VERSION, self.id, device)
        print(f"Intersection with {device} - {cs.__class__.__name__} - Result: {multiplied_set}")

    @log_activity
    def handle_psi_ca_ope(self, device, cs, coeffs, pubkey):
        my_data = [int(element) for element in self.my_data]
        pubkey = cs.reconstruct_public_key(pubkey)
        coeffs = cs.get_encrypted_list(coeffs, pubkey)
        result = cs.get_evaluations(coeffs, pubkey, my_data)
        return result

    @log_activity
    def final_step_psi_ca_ope(self, device, cs, peer_data):
        result = cs.get_encrypted_list_f(peer_data['data'])
        result = [int(cs.decrypt(encrypted_value)) for encrypted_value in result]
        print(f"Intersection with {peer_data['peer']} - {cs.__class__.__name__} PSI-CA OPE - Raw results: {result}")
        # When the element is 0, it means it's in the intersection
        cardinality = sum([int(element == 0) for element in result])
        self.results[device] = cardinality
        Logs.log_result((cs.__class__.__name__ + '_PSI-CA_OPE'), cardinality, VERSION, self.id, device)
        print(f"Cardinality calculation with {device} - {cs.__class__.__name__} PSI-CA OPE - Result: {cardinality}")

    def test_launcher(self, device):
        cs_list = [self.paillier, self.damgard_jurik]
        threads = [threading.Thread(target=self.intersection_first_step, args=(device, cs)) for _ in range(TEST_ROUNDS)
                   for cs in cs_list]
        threads += [threading.Thread(target=self.intersection_first_step_ope, args=(device, cs)) for _ in
                    range(TEST_ROUNDS) for cs in cs_list]
        threads += [threading.Thread(target=self.intersection_first_step_ope, args=(device, cs, "PSI-CA")) for _ in
                    range(TEST_ROUNDS) for cs in cs_list]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(lambda t: t.start(), threads)
            executor.map(lambda t: t.join(), threads)

    def genkeys(self, cs):
        start_time = time.time()
        Logs.start_logging(ThreadData())
        key_instances = {"Paillier": Paillier(), "Damgard-Jurik": DamgardJurik()}
        if cs in key_instances:
            setattr(self, cs.lower().replace('-', '_'), key_instances[cs])
        end_time = time.time()
        Logs.stop_logging(ThreadData())
        Logs.log_activity(ThreadData(), "GENKEYS_" + cs, end_time - start_time, VERSION, self.id)
