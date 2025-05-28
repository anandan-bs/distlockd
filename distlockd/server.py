import asyncio
import time
import logging
import signal
import struct
import sys
from typing import Dict, Any

from .protocol import BinaryProtocol

from .constants import (
    CMD_ACQUIRE,
    CMD_RELEASE,
    CMD_HEALTH,
    RESP_OK,
    RESP_ERROR,
    RESP_TIMEOUT,
    RESP_INVALID,
    STALE_LOCK_TIMEOUT,
    CMD_FORMAT,
    CMD_HEADER_SIZE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
locks: Dict[str, Dict[str, Any]] = {}

shutdown_event = asyncio.Event()

async def cleanup_stale_locks() -> None:
    """Periodically clean up stale locks."""
    while not shutdown_event.is_set():
        try:
            now = time.time()
            # Process locks in batches for better performance
            stale = [name for name, lock in locks.items()
                    if now - lock['time'] > STALE_LOCK_TIMEOUT]

            if stale:
                logger.debug(f"Cleaning up {len(stale)} stale locks")
                for name in stale:
                    locks.pop(name, None)  # None as default to avoid KeyError
            else:
                logger.debug("No stale locks found")

            # Exponential backoff waiting logic
            sleep_time = 0.1
            while not shutdown_event.is_set():
                await asyncio.sleep(sleep_time)
                sleep_time *= 2
                if sleep_time > 10:
                    sleep_time = 10
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(5)

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Handle client connections and lock operations."""
    peer = writer.get_extra_info('peername')
    logger.info(f"New client connection from {peer} accepted.")

    # Keep connection alive until error or client disconnects
    while not reader.at_eof() and not shutdown_event.is_set():
        try:
            # Read header first (5 bytes: cmd_type + name_len + client_id_len)
            header = await reader.readexactly(CMD_HEADER_SIZE)
            cmd_type, name_len, client_id_len = struct.unpack(CMD_FORMAT, header)

            # Read name and client_id
            data = await reader.readexactly(name_len + client_id_len)

            name = data[:name_len].decode('utf-8')
            client_id = data[name_len:].decode('utf-8')

            # Process command
            if cmd_type == CMD_ACQUIRE:
                logger.debug(f"Received command: type=acquire, name={name}, client={client_id}")
                if name in locks and locks[name]['client'] != client_id:
                    response = BinaryProtocol.pack_response(RESP_TIMEOUT, "Lock is busy")
                else:
                    locks[name] = {'client': client_id, 'time': time.time()}
                    response = BinaryProtocol.pack_response(RESP_OK)
                logger.debug(f"Acquired lock: {name}, client={client_id}")
            elif cmd_type == CMD_RELEASE:
                logger.debug(f"Received command: type=release, name={name}, client={client_id}")
                if name in locks and locks[name]['client'] == client_id:
                    locks.pop(name)
                    response = BinaryProtocol.pack_response(RESP_OK)
                    logger.debug(f"Released lock: {name}, client={client_id}")
                else:
                    response = BinaryProtocol.pack_response(RESP_ERROR, "Invalid release")
                    logger.error(f"Failed to release lock: {name}, client={client_id}")
            elif cmd_type == CMD_HEALTH:
                logger.debug(f"Received command: type=health, name={name}, client={client_id}")
                response = BinaryProtocol.pack_response(RESP_OK)
                logger.debug(f"Health check passed for lock: {name}, client={client_id}")
            else:
                logger.debug(f"Received command: type=invalid command, name={name}, client={client_id}")
                response = BinaryProtocol.pack_response(RESP_INVALID, "Invalid command")
                logger.error(f"Invalid command received: {name}, client={client_id}")

            # Write response and wait for it to be sent
            writer.write(response)
            await writer.drain()

        except asyncio.IncompleteReadError:
            # Client disconnected
            logger.debug(f"Client {peer} disconnected")
            break
        except asyncio.TimeoutError:
            logger.debug(f"Timeout reading from client {peer}")
            break
        except ConnectionError as e:
            logger.debug(f"Connection error with {peer}: {e}")
            break
        except Exception as e:
            logger.debug(f"Unexpected error handling client {peer}: {e}")
            break

    # Only close the connection when we're done with the client
    try:
        writer.close()
        await writer.wait_closed()
        logger.info(f"Closed connection to {peer}")
    except Exception as e:
        logger.critical(f"Error closing connection to {peer}: {e}")

async def shutdown(signal: signal.Signals, loop: asyncio.AbstractEventLoop) -> None:
    """Handle graceful shutdown on signal."""
    logger.info(f"Received exit signal {signal.name}...")
    shutdown_event.set()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

async def main(host: str, port: int, verbose: bool = False) -> None:
    """Main server function."""
    if verbose:
        logger.setLevel(logging.DEBUG)
    logger.info("Starting distlockd server...")
    try:
        # Create the server
        try:
            server = await asyncio.start_server(
                handle_client,
                host,
                port,
                reuse_address=True
            )
        except OSError as e:
            logger.error(f"Failed to bind to port {port}: {e}")
            sys.exit(1)

        # Start cleanup task
        cleanup_task = asyncio.create_task(cleanup_stale_locks())

        # Run the server
        async with server:
            addr = server.sockets[0].getsockname()
            logger.info(f"distlockd server running on {addr[0]}:{addr[1]}")
            try:
                await server.serve_forever()
            except asyncio.CancelledError:
                logger.info("Server shutdown initiated")

    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        if 'cleanup_task' in locals():
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass