import concurrent.futures
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from flaskr import Logs, Node
from flaskr.handlers.IntersectionHandler import IntersectionHandler
from flaskr.helpers.CryptoImplementation import CryptoImplementation
from flaskr.helpers.DbConstants import VERSION, TEST_ROUNDS
from flaskr.Logs import ThreadData
from flaskr.handlers.DamgardJurikHandler import DamgardJurikHandler
from flaskr.handlers.PaillierHandler import PaillierHandler
from flaskr.helpers.Polynomials import polinomio_raices


class SchemeHandler:
    def __init__(self):
        self.CSHandlers = {
            CryptoImplementation("Paillier", "Paillier OPE", "Paillier_OPE",
                                 "Paillier PSI-CA OPE"): PaillierHandler(),
            CryptoImplementation("DamgardJurik", "Damgard-Jurik", "DamgardJurik OPE", "Damgard-Jurik_OPE",
                                 "DamgardJurik PSI-CA OPE", "Damgard-Jurik PSI-CA OPE"): DamgardJurikHandler()
        }
        self.intersectionHandler = IntersectionHandler()
        self.id = Node.getinstance().id
        self.devices = Node.getinstance().devices
        self.executor = ThreadPoolExecutor(max_workers=10)

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
        key_instances = {"Paillier": PaillierHandler(), "Damgard-Jurik": DamgardJurikHandler()}
        if cs in key_instances:
            setattr(self, cs.lower().replace('-', '_'), key_instances[cs])
        end_time = time.time()
        Logs.stop_logging(ThreadData())
        Logs.log_activity(ThreadData(), "GENKEYS_" + cs, end_time - start_time, VERSION, self.id)

    def handle_message(self, message):
        if "cryptpscheme" in message and "peer" in message:
            self.handle_intersection(message)
        else:
            self.handle_second_step(message)

    def start_intersection(self, device, scheme, type):
        crypto_impl = CryptoImplementation.from_string(scheme)
        if crypto_impl in self.CSHandlers:
            cs = self.CSHandlers[crypto_impl]
            if type == "OPE" or type == "PSI-CA":
                self.executor.submit(self.intersectionHandler.intersection_first_step_ope, device, cs, type)
            else:
                self.executor.submit(self.intersectionHandler.intersection_first_step, device, cs)
            return "Intersection started"
        return "Invalid scheme: " + scheme

    def send_message(self, peer_data, set, cryptpscheme):
        set_to_send = {}
        if cryptpscheme == "Paillier":
            set_to_send = {element: str(encrypted_value.ciphertext()) for element, encrypted_value in set.items()}
        elif cryptpscheme == "Damgard-Jurik" or cryptpscheme == "DamgardJurik":
            set_to_send = {element: str(encrypted_value.value) for element, encrypted_value in set.items()}
        elif cryptpscheme == "Paillier_OPE" or cryptpscheme == "Paillier OPE" or cryptpscheme == "Paillier PSI-CA OPE":
            set_to_send = [str(encrypted_value.ciphertext()) for encrypted_value in set]
        elif (cryptpscheme == "Damgard-Jurik_OPE" or cryptpscheme == "DamgardJurik OPE" or
              cryptpscheme == "Damgard-Jurik PSI-CA OPE"):
            set_to_send = [str(encrypted_value.value) for encrypted_value in set]
        message = {'data': set_to_send, 'peer': self.id, 'cryptpscheme': cryptpscheme}
        self.devices[peer_data['peer']]["socket"].send_json(message)
