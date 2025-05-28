"""
Constants used throughout the distlockd package.
"""
from typing import Final
import multiprocessing

# Default configuration
DEFAULT_HOST: Final = "localhost"
DEFAULT_PORT: Final = 9999
DEFAULT_TIMEOUT: Final = 5.0
DEFAULT_RETRY_COUNT: Final = 3
DEFAULT_RETRY_DELAY: Final = 0.5
STALE_LOCK_TIMEOUT: Final = 3600  # seconds
MAX_CONNECTIONS: Final = multiprocessing.cpu_count() * 2 # int

# Protocol constants
CMD_ACQUIRE = 0x01
CMD_RELEASE = 0x02
CMD_HEALTH = 0x03

RESP_OK = 0x00
RESP_ERROR = 0x01
RESP_TIMEOUT = 0x02
RESP_INVALID = 0x03

# Protocol format constants
CMD_FORMAT = "!BHH"  # Format for command header: cmd_type(1) + name_len(2) + client_id_len(2)
RESP_FORMAT = "!BH"  # Format for response header: status(1) + msg_len(2)
CMD_HEADER_SIZE = 5   # Size of command header in bytes
RESP_HEADER_SIZE = 3  # Size of response header in bytes
