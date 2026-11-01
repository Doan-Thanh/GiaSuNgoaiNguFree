import socket
import logging

logger = logging.getLogger("ThanhBooksAI.PortFinder")

SYSTEM_BLACKLIST_PORTS = {
    9876, 8720, 8721, 3888, 8501, 8502, 9222, 9223, 48900, 53100, 8000, 8080, 3000, 5000
}

def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    if port in SYSTEM_BLACKLIST_PORTS:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            return True
    except OSError:
        return False

def find_safe_port(start_port: int = 53210, end_port: int = 53290, host: str = "127.0.0.1") -> int:
    for port in range(start_port, end_port):
        if port in SYSTEM_BLACKLIST_PORTS:
            continue
        if is_port_available(port, host):
            return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]
