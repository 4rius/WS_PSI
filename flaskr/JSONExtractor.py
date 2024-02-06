import json

from flaskr.implementations.Damgard_jurik import reconstruct_public_key_dj
from flaskr.implementations.Paillier import reconstruct_public_key


def extract_peer_data(message):
    try:
        peer_data = json.loads(message)
        if 'peer' in peer_data:
            peer_data['peer'] = peer_data.pop('peer')
        if 'implementation' in peer_data:
            peer_data['implementation'] = peer_data.pop('implementation')
            if peer_data['implementation'] == "Paillier" and 'pubkey' in peer_data:
                peer_data['pubkey'] = reconstruct_public_key(peer_data['pubkey'])
            elif peer_data['implementation'] == "Damgard-Jurik" and 'pubkey' in peer_data:
                peer_data['pubkey'] = reconstruct_public_key_dj(peer_data['pubkey'])
        return peer_data
    except json.JSONDecodeError:
        print("Received message is not a valid JSON.")
        return "Received message is not a valid JSON."
