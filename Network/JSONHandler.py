import json
import time

from Crypto.helpers.BFVHelper import BFVHelper
from Logs import Logs
from Logs.Logs import ThreadData
from Crypto.handlers.CAOPEHandler import CAOPEHandler
from Crypto.helpers.DamgardJurikHandler import DamgardJurikHelper
from Crypto.handlers.DomainPSIHandler import DomainPSIHandler
from Crypto.handlers.OPEHandler import OPEHandler
from Crypto.helpers.PaillierHandler import PaillierHelper
from Crypto.helpers.CryptoImplementation import CryptoImplementation
from Network.PriorityExecutor import PriorityExecutor
from Network.collections.DbConstants import VERSION, TEST_ROUNDS


# Priorities
# 0: Intersection first step
# 1: Intersection second step
# 2: Intersection final step
# 1 and 2 will be executed first to stop consuming memory on the queue
class JSONHandler:
    def __init__(self, id, my_data, domain, devices, results, new_peer_function):
        self.CSHandlers = {
            CryptoImplementation("Paillier", "Paillier OPE", "Paillier_OPE",
                                 "Paillier PSI-CA OPE"): PaillierHelper(),
            CryptoImplementation("DamgardJurik", "Damgard-Jurik", "DamgardJurik OPE",
                                 "Damgard-Jurik_OPE", "Damgard-Jurik OPE", "DamgardJurik PSI-CA OPE",
                                 "Damgard-Jurik PSI-CA OPE"): DamgardJurikHelper(),
            CryptoImplementation("BFV_OPE", "BFV OPE"): BFVHelper()
        }
        self.OPEHandler = OPEHandler(id, my_data, domain, devices, results)
        self.CAOPEHandler = CAOPEHandler(id, my_data, domain, devices, results)
        self.domainPSIHandler = DomainPSIHandler(id, my_data, domain, devices, results)
        self.id = id
        self.devices = devices
        self.executor = PriorityExecutor(max_workers=10)
        self.new_peer = new_peer_function

    def test_launcher(self, device):
        cs_handlers = self.CSHandlers.values()
        for _ in range(TEST_ROUNDS):
            for cs in cs_handlers:
                self.executor.submit(0, self.domainPSIHandler.intersection_first_step, device, cs)
                self.executor.submit(0, self.OPEHandler.intersection_first_step, device, cs)
                self.executor.submit(0, self.CAOPEHandler.intersection_first_step, device, cs)

    def genkeys(self, cs, bit_length):
        start_time = time.time()
        Logs.start_logging(ThreadData())
        self.CSHandlers[CryptoImplementation.from_string(cs)].generate_keys(bit_length)
        end_time = time.time()
        Logs.stop_logging(ThreadData())
        print("Key generation - " + cs + " - Time: " + str(end_time - start_time) + "s")
        Logs.log_activity(ThreadData(), "GENKEYS_" + cs, end_time - start_time, VERSION, self.id)

    def start_intersection(self, device, scheme, type, rounds) -> str:
        crypto_impl = CryptoImplementation.from_string(scheme)
        if crypto_impl in self.CSHandlers:
            cs = self.CSHandlers[crypto_impl]
            if type == "OPE":
                for _ in range(int(rounds)):
                    self.executor.submit(0, self.OPEHandler.intersection_first_step, device, cs)
            elif type == "PSI-CA":
                for _ in range(int(rounds)):
                    self.executor.submit(0, self.CAOPEHandler.intersection_first_step, device, cs)
            elif type == "PSI-Domain":
                for _ in range(int(rounds)):
                    self.executor.submit(0, self.domainPSIHandler.intersection_first_step, device, cs)
            else:
                return "Invalid type: " + type
            return ("Intersection with " + device + " - " + scheme + " - " + type + " - Rounds: " + str(rounds) +
                    " - Task started, check logs")
        return "Invalid scheme: " + scheme

    def handle_message(self, message):
        try:
            message = json.loads(message)
            print(f"Node {self.id} (You) received: {message}")
            if message['peer'] not in self.devices:
                self.new_peer(message['peer'], time.strftime("%H:%M:%S", time.localtime()))
            if message['step'] == "2":
                self.handle_intersection_second_step(message)
            elif message['step'] == "F":
                self.handle_intersection_final_step(message)
        except json.JSONDecodeError:
            print("Received message is not a valid JSON.")

    def handle_intersection_second_step(self, message):
        crypto_impl = CryptoImplementation.from_string(message['implementation'])
        if crypto_impl in self.CSHandlers:
            cs = self.CSHandlers[crypto_impl]
            if "PSI-CA" in message['implementation']:
                self.executor.submit(1, self.CAOPEHandler.intersection_second_step, message['peer'],
                                     cs, message['data'], message['pubkey'])
            elif "OPE" in message['implementation']:
                self.executor.submit(1, self.OPEHandler.intersection_second_step, message['peer'], cs,
                                     message['data'], message['pubkey'])
            else:
                self.executor.submit(1, self.domainPSIHandler.intersection_second_step, message['peer'], cs,
                                     message['data'], message['pubkey'])
        else:
            Exception("Invalid scheme: " + message['implementation'])

    def handle_intersection_final_step(self, message):
        crypto_impl = CryptoImplementation.from_string(message['implementation'])
        if crypto_impl in self.CSHandlers:
            cs = self.CSHandlers[crypto_impl]
            if "PSI-CA" in message['implementation']:
                self.executor.submit(2, self.CAOPEHandler.intersection_final_step, message['peer'], cs,
                                     message['data'])
            elif "OPE" in message['implementation']:
                self.executor.submit(2, self.OPEHandler.intersection_final_step, message['peer'], cs,
                                     message['data'])
            else:
                self.executor.submit(2, self.domainPSIHandler.intersection_final_step, message['peer'], cs,
                                     message['data'])
        else:
            Exception("Invalid scheme: " + message['implementation'])
