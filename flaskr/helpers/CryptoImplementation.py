class CryptoImplementation:
    entries = {}

    def __init__(self, *aliases):
        for alias in aliases:
            CryptoImplementation.entries[alias] = self

    @staticmethod
    def from_string(text):
        return CryptoImplementation.entries.get(text)