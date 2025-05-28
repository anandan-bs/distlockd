"""
distlockd.client

Client for the distlockd lock server.
"""
import uuid
import logging
import time
import struct
from typing import Optional, Any
from contextlib import contextmanager

from .exceptions import (
    LockAcquisitionTimeout,
    LockReleaseError,
    ServerError,
    ConnectionError
)
from .protocol import BinaryProtocol
from .connection_pool import ConnectionPool

from .constants import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    CMD_ACQUIRE,
    CMD_RELEASE,
    CMD_HEALTH,
    RESP_OK,
    RESP_TIMEOUT,
    MAX_CONNECTIONS,
    DEFAULT_RETRY_COUNT,
    DEFAULT_RETRY_DELAY,
    DEFAULT_TIMEOUT
)


logger = logging.getLogger(__name__)

class Client:
    """Client for the distlockd lock server.

    Example usage:

    Basic setup:
    ```python
    from distlockd.client import Client
    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create a client
    client = Client(host='localhost', port=8888)

    # Check server health
    if client.check_server_health():
        print("Server is healthy!")
    ```

    Manual lock management:
    ```python
    # Acquire a lock
    if client.acquire("resource-1", timeout=5.0):
        try:
            print("Lock acquired, doing work...")
            # Critical section here
        finally:
            # Always release the lock
            client.release("resource-1")
    ```

    Using context manager (recommended):
    ```python
    try:
        with client.lock("resource-1", timeout=3.0):
            print("Lock acquired via context manager")
            # Critical section here
            # Lock is automatically released when block exits
    except Exception as e:
        print(f"Error: {e}")
    ```

    Error handling:
    ```python
    from distlockd.exceptions import LockAcquisitionTimeout, LockReleaseError

    try:
        with client.lock("resource-1"):
            # Critical section
            pass
    except LockAcquisitionTimeout:
        print("Failed to acquire lock: timeout")
    except LockReleaseError as e:
        print(f"Error releasing lock: {e}")
    ```
    """
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        retry_count: int = DEFAULT_RETRY_COUNT,
        connect_timeout: float = DEFAULT_RETRY_DELAY,
        operation_timeout: float = DEFAULT_TIMEOUT,
        pool_size: int = MAX_CONNECTIONS
    ) -> None:
        self.host = host
        self.port = port
        self.retry_count = retry_count
        self.connect_timeout = connect_timeout
        self.operation_timeout = operation_timeout
        self.client_id = str(uuid.uuid4())
        self._pool = ConnectionPool(host, port, pool_size)
        logger.debug(f"Initialized client {self.client_id} for {host}:{port}")

    def _send_binary(self, cmd_type: int, name: str) -> tuple[int, str]:
        """Send a binary command to the server with retry logic and pooling."""
        retries = self.retry_count
        last_error = None

        for attempt in range(retries):
            sock = None
            try:
                # Pack command
                cmd = BinaryProtocol.pack_command(cmd_type, name, self.client_id)

                # Send command
                sock = self._pool.get()
                sock.sendall(cmd)

                # Read response header (3 bytes: status + msg_len)
                header = sock.recv(3)
                if len(header) < 3:
                    raise ServerError("Incomplete response header")
                status, msg_len = struct.unpack('!BH', header)
                # Read message if any
                message = b''
                if msg_len > 0:
                    message = sock.recv(msg_len)
                    if len(message) < msg_len:
                        raise ServerError("Incomplete response message")
                self._pool.put(sock)
                return status, message.decode('utf-8') if message else ''

            except (socket.timeout, socket.error, ServerError) as e:
                last_error = e
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass
                if attempt < retries - 1:
                    logger.warning(
                        f"Connection attempt {attempt + 1} failed: {e}. Retrying..."
                    )
                    time.sleep(0.1)
                continue

        raise ConnectionError(
            f"Failed to communicate with server after {retries} attempts",
            host=self.host,
            port=self.port,
            attempt=retries,
            cause=str(last_error)
        )

    def check_server_health(self) -> bool:
        """Check if server is responding."""
        try:
            status, _ = self._send_binary(CMD_HEALTH, 'health')
            return status == RESP_OK
        except Exception:
            return False

    def acquire(self, name: str, timeout: Optional[float] = None) -> bool:
        """Acquire a named lock with timeout."""
        if not name:
            raise ValueError("Lock name cannot be empty")

        start = time.time()
        attempt = 0
        logger.debug(f"Attempting to acquire lock: {name}")

        while True:
            try:
                status, _ = self._send_binary(CMD_ACQUIRE, name)
                if status == RESP_OK:
                    self.current_lock = name
                    logger.info(f"Successfully acquired lock: {name}")
                    return True
                elif status == RESP_TIMEOUT:
                    if timeout and (time.time() - start >= timeout):
                        raise LockAcquisitionTimeout(
                            f"Failed to acquire lock: {name}",
                            lock_name=name,
                            timeout=timeout,
                            attempts=attempt
                        )
                    attempt += 1
                    logger.debug(
                        f"Lock {name} is busy, attempt {attempt}. Waiting..."
                    )
                    time.sleep(0.1)
                else:
                    raise ServerError(f"Unexpected response from server: {status}")
            except ConnectionError as e:
                if timeout and (time.time() - start >= timeout):
                    raise
                logger.warning(f"Connection error while acquiring lock: {e}")
                time.sleep(0.1)

    def release(self, name: str) -> bool:
        """Release a named lock.

        Args:
            name: Name of the lock to release.

        Returns:
            bool: True if the lock was successfully released, False otherwise.
        """
        try:
            status, message = self._send_binary(CMD_RELEASE, name)

            if status == RESP_OK:
                # If this was our current lock, clear it
                if self.current_lock == name:
                    self.current_lock = None
                logger.info(f"Successfully released lock: {name}")
                return True
            else:
                raise LockReleaseError(
                    f"Failed to release lock {name}: {message}"
                )
        except Exception as e:
            raise LockReleaseError(
                f"Error releasing lock {name}",
                error=e
            )

    @contextmanager
    def lock(self, name: str, timeout: Optional[float] = None) -> Any:
        """Context manager for acquiring and releasing a lock."""
        acquired = False
        try:
            acquired = self.acquire(name, timeout)
            yield self
        finally:
            if acquired:
                try:
                    self.release(name)
                except Exception as e:
                    logger.error(f"Error releasing lock in context manager: {e}")