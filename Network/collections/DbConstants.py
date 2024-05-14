VERSION = '2.0 - DEV WS'

DEFL_DOMAIN = 500
DOM_BFV = 100003
DEFL_SET_SIZE = 50
DEFL_PORT = 5001

DEFL_KEYSIZE_PAILLIER = 2048
DEFL_KEYSIZE_DAMGARD = 128
DEFL_EXPANSIONFACTOR = 2

TEST_ROUNDS = 20  # This would be 20 * 6 type of operations, so 120 operations in total

FB_URL = 'https://tfg-en-psi-default-rtdb.europe-west1.firebasedatabase.app'


def update_dfl_domain(new_domain):
    global DEFL_DOMAIN
    DEFL_DOMAIN = new_domain
    global DOM_BFV
    DOM_BFV = DEFL_DOMAIN * 2 if DEFL_DOMAIN % 2 != 0 else DEFL_DOMAIN * 2 + 1