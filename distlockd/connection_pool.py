import socket
import threading

from distlockd.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    MAX_CONNECTIONS
)

class ConnectionPool:
    def __init__(self, host: str=DEFAULT_HOST, port: int=DEFAULT_PORT, max_connections: int=MAX_CONNECTIONS):
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            if self.connections:
                return self.connections.pop()
            else:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self.host, self.port))
                    return sock
                except Exception as e:
                    raise ConnectionError(f"Error creating connection: {e}")

    def put(self, sock):
        with self.lock:
            self.connections.append(sock)

    def close_all(self):
        with self.lock:
            for sock in self.connections:
                sock.close()
            self.connections = []