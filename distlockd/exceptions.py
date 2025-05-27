"""
Exceptions raised by the distlockd client.
"""

class DistLockError(Exception):
    """Base exception for all distlockd errors."""
    def __init__(self, message: str, *, cause: str = None, details: dict = None):
        super().__init__(message)
        self.cause = cause or "Unknown cause"
        self.details = details or {}

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base_msg} (Cause: {self.cause}, Details: {details_str})"
        return f"{base_msg} (Cause: {self.cause})"

class ConnectionError(DistLockError):
    """Raised when there are network communication issues."""
    def __init__(self, message: str, *, host: str = None, port: int = None,
                 attempt: int = None, cause: str = None):
        details = {
            'host': host,
            'port': port,
            'attempt': attempt
        }
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, cause=cause or "Network communication failure", details=details)

class ServerError(DistLockError):
    """Raised when the server returns an unexpected response."""
    def __init__(self, message: str, *, response: str = None, command: str = None):
        details = {
            'response': response,
            'command': command
        }
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, cause="Unexpected server response", details=details)

class LockAcquisitionTimeout(DistLockError):
    """Raised when a lock cannot be acquired within the timeout period."""
    def __init__(self, message: str, *, lock_name: str = None, timeout: float = None,
                 attempts: int = None):
        details = {
            'lock_name': lock_name,
            'timeout': timeout,
            'attempts': attempts
        }
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, cause="Lock acquisition timeout", details=details)

class LockReleaseError(DistLockError):
    """Raised when a lock cannot be released by the current client."""
    def __init__(self, message: str, *, lock_name: str = None, client_id: str = None,
                 owner_id: str = None):
        details = {
            'lock_name': lock_name,
            'client_id': client_id,
            'owner_id': owner_id
        }
        details = {k: v for k, v in details.items() if v is not None}
        super().__init__(message, cause="Lock release denied", details=details)