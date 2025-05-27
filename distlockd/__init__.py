"""
distlockd - A lightweight distributed lock server.
"""

from .client import Client
from .exceptions import (
    LockAcquisitionTimeout,
    LockReleaseError,
    ServerError,
    ConnectionError
)


__version__ = '0.1.0'
__all__ = [
    'Client',
    'LockAcquisitionTimeout',
    'LockReleaseError',
    'ServerError',
    'ConnectionError'
]