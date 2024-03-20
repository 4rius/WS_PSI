import json
import time
from concurrent.futures import ThreadPoolExecutor

from flaskr import Logs, Node
from flaskr.Logs import ThreadData
from flaskr.handlers.DamgardJurikHandler import DamgardJurikHandler
from flaskr.handlers.IntersectionHandler import IntersectionHandler
from flaskr.handlers.PaillierHandler import PaillierHandler
from flaskr.helpers.CryptoImplementation import CryptoImplementation
from flaskr.helpers.DbConstants import VERSION, TEST_ROUNDS


class SchemeHandler:
    def __init__(self, id, my_data, domain, devices, results):
        self.CSHandlers = {
            CryptoImplementation("Paillier", "Paillier OPE", "Paillier_OPE",
                                 "Paillier PSI-CA OPE"): PaillierHandler(),
            CryptoImplementation("DamgardJurik", "Damgard-Jurik", "DamgardJurik OPE", "Damgard-Jurik_OPE",
                                 "Damgard-Jurik OPE", "DamgardJurik PSI-CA OPE", "Damgard-Jurik PSI-CA OPE"): DamgardJurikHandler()
        }
        self.intersectionHandler = IntersectionHandler(id, my_data, domain, devices, results)
        self.id = id
        self.devices = devices
        self.executor = ThreadPoolExecutor(max_workers=10)

    def test_launcher(self, device):
        cs_handlers = self.CSHandlers.values()
        for _ in range(TEST_ROUNDS):
            for cs in cs_handlers:
                self.executor.submit(self.intersectionHandler.intersection_first_step, device, cs)
                self.executor.submit(self.intersectionHandler.intersection_first_step_ope, device, cs, "PSI")
                self.executor.submit(self.intersectionHandler.intersection_first_step_ope, device, cs, "PSI-CA")

    def genkeys(self, cs):
        start_time = time.time()
        Logs.start_logging(ThreadData())
        self.CSHandlers[CryptoImplementation.from_string(cs)].generate_keys()
        end_time = time.time()
        Logs.stop_logging(ThreadData())
        Logs.log_activity(ThreadData(), "GENKEYS_" + cs, end_time - start_time, VERSION, self.id)

    def start_intersection(self, device, scheme, type):
        crypto_impl = CryptoImplementation.from_string(scheme)
        if crypto_impl in self.CSHandlers:
            cs = self.CSHandlers[crypto_impl]
            if type == "OPE" or type == "PSI-CA":
                self.executor.submit(self.intersectionHandler.intersection_first_step_ope, device, cs, type)
            else:
                self.executor.submit(self.intersectionHandler.intersection_first_step, device, cs)
            return "Intersection with " + device + " - " + scheme + " - Thread started, check logs"
        return "Invalid scheme: " + scheme

    def handle_message(self, message):
        if "cryptpscheme" in message and "peer" in message:
            self.handle_intersection_final_step(message)
        else:
            self.handle_intersection_second_step(message)

    def handle_intersection_second_step(self, message):
        try:
            message = json.loads(message)
            if message['peer'] not in self.devices:
                Node.getinstance().new_peer(message['peer'], time.strftime("%H:%M:%S", time.localtime()))
            crypto_impl = CryptoImplementation.from_string(message['implementation'])
            if crypto_impl in self.CSHandlers:
                cs = self.CSHandlers[crypto_impl]
                if "PSI-CA" in message['implementation']:
                    self.executor.submit(self.intersectionHandler.intersection_second_step_psi_ca_ope, message['peer'],
                                         cs, message['data'], message['pubkey'])
                elif "OPE" in message['implementation']:
                    self.executor.submit(self.intersectionHandler.intersection_second_step_ope, message['peer'], cs,
                                         message['data'], message['pubkey'])
                else:
                    self.executor.submit(self.intersectionHandler.intersection_second_step, message['peer'], cs,
                                         message['data'], message['pubkey'])
            else:
                Exception("Invalid scheme: " + message['implementation'])
        except json.JSONDecodeError:
            print("Received message is not a valid JSON.")

    def handle_intersection_final_step(self, message):
        try:
            message = json.loads(message)
            crypto_impl = CryptoImplementation.from_string(message['cryptpscheme'])
            if crypto_impl in self.CSHandlers:
                cs = self.CSHandlers[crypto_impl]
                if "PSI-CA" in message['cryptpscheme']:
                    self.executor.submit(self.intersectionHandler.final_step_psi_ca_ope, message['peer'], cs,
                                         message['data'])
                elif "OPE" in message['cryptpscheme']:
                    self.executor.submit(self.intersectionHandler.intersection_final_step_ope, message['peer'], cs,
                                         message['data'])
                else:
                    self.executor.submit(self.intersectionHandler.intersection_final_step, message['peer'], cs,
                                         message['data'])
            else:
                Exception("Invalid scheme: " + message['cryptpscheme'])
        except json.JSONDecodeError:
            print("Received message is not a valid JSON.")
