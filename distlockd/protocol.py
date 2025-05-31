"""
Protocol handlers for distlockd server commands.
"""
import logging
import struct
from typing import Tuple

from .constants import CMD_FORMAT, RESP_FORMAT, CMD_HEADER_SIZE, RESP_HEADER_SIZE

logger = logging.getLogger(__name__)

class BinaryProtocol:
    """Binary protocol for client-server communication."""
    @staticmethod
    def pack_command(cmd_type: int, name: str, client_id: str) -> bytes:
        """Pack a command into binary format.
        Format: <cmd_type:1><name_len:2><client_id_len:2><name><client_id>
        """
        name_bytes = name.encode('utf-8')
        client_id_bytes = client_id.encode('utf-8')
        header = struct.pack(
            CMD_FORMAT,  # network byte order, unsigned char + 2 unsigned shorts
            cmd_type,
            len(name_bytes),
            len(client_id_bytes)
        )
        return header + name_bytes + client_id_bytes

    @staticmethod
    def unpack_command(data: bytes) -> Tuple[int, str, str]:
        """Unpack a binary command."""
        cmd_type, name_len, client_id_len = struct.unpack(CMD_FORMAT, data[:CMD_HEADER_SIZE])
        name = data[CMD_HEADER_SIZE:CMD_HEADER_SIZE+name_len].decode('utf-8')
        client_id = data[CMD_HEADER_SIZE+name_len:CMD_HEADER_SIZE+name_len+client_id_len].decode('utf-8')
        return cmd_type, name, client_id

    @staticmethod
    def pack_response(status: int, message: str = '') -> bytes:
        """Pack a response into binary format.
        Format: <status:1><msg_len:2><message>
        """
        message_bytes = message.encode('utf-8') if message else b''
        header = struct.pack(RESP_FORMAT, status, len(message_bytes))
        return header + message_bytes

    @staticmethod
    def unpack_response(data: bytes) -> Tuple[int, str]:
        """Unpack a binary response."""
        status, msg_len = struct.unpack(RESP_FORMAT, data[:RESP_HEADER_SIZE])
        message = data[RESP_HEADER_SIZE:RESP_HEADER_SIZE+msg_len].decode('utf-8') if msg_len > 0 else ''
        return status, message