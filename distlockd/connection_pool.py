"""
Module implementing a connection pool for distlockd clients.

A connection pool is a cache of database connections that can be reused to
improve performance for applications that open and close connections frequently.
The pool is thread-safe and allows connections to be reused, which can
improve performance for applications that open and close connections
frequently.

"""

import socket
import threading

from .constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    MAX_CONNECTIONS
)

class ConnectionPool:
    """
    Manages a pool of connections to a server.

    The pool is thread-safe and allows connections to be reused, which can
    improve performance for applications that open and close connections
    frequently.

    :param host: Hostname or IP address of the server. Defaults to
        ``distlockd.constants.DEFAULT_HOST``.
    :param port: Port number of the server. Defaults to
        ``distlockd.constants.DEFAULT_PORT``.
    :param max_connections: Maximum number of connections in the pool.
        Defaults to ``distlockd.constants.MAX_CONNECTIONS``.
    """

    def __init__(self, host: str=DEFAULT_HOST, port: int=DEFAULT_PORT, max_connections: int=MAX_CONNECTIONS):
        """
        Initializes the connection pool.

        :param host: Hostname or IP address of the server.
        :param port: Port number of the server.
        :param max_connections: Maximum number of connections in the pool.
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get(self):
        """
        Gets a connection from the pool.

        If there are no available connections, a new one is created. If the
        maximum number of connections has been reached, a ``ConnectionError`` is
        raised.
        """
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
        """
        Returns a connection to the pool.

        :param sock: Socket to return to the pool.
        """
        with self.lock:
            self.connections.append(sock)

    def close_all(self):
        """
        Closes all connections in the pool.
        """
        with self.lock:
            for sock in self.connections:
                sock.close()
            self.connections = []