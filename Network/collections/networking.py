import platform
import socket


def get_local_ip():
    system = platform.system()

    # macOS y Linux
    if system == "Linux" or system == "Darwin":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 80))  # No tiene ni que ser un host real
            ip = s.getsockname()[0]
            s.close()
            # Si es ipv6 la tenemos que devolver entre corchetes
            if ":" in ip:
                return "[" + ip + "]"
            return ip
        except OSError:
            print("Error fetching IP, using loopback")
    # Windows y errores de macOS y Linux tiran por aquí
    ip = socket.gethostbyname(socket.gethostname())
    if ":" in ip:
        return "[" + ip + "]"
    return ip


def is_valid_ipv4(peer):
    try:
        octets = peer.split(".")
        if len(octets) != 4:
            return False
        for octet in octets:
            if not 0 <= int(octet) <= 255:
                return False
    except ValueError:
        return False

    return True


def is_valid_ipv6(peer):
    try:
        hextets = peer.split(":")
        if len(hextets) != 8:
            return False
        for hextet in hextets:
            if not 0 <= int(hextet, 16) <= 65535:
                return False
    except ValueError:
        return False

    return True
