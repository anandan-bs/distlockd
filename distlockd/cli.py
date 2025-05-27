"""
Command-line interface for distlockd server.
"""
import argparse
import asyncio
import logging
from typing import Optional

from .server import LockServer

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='distlockd - A lightweight distributed lock server')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Server command
    server_parser = subparsers.add_parser('server', help='Start the distlockd server')
    server_parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )
    server_parser.add_argument(
        '-p', '--port',
        type=int,
        default=8888,
        help='Port to listen on (default: 8888)'
    )
    server_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    return parser.parse_args()

async def start_server(host: str, port: int, verbose: bool = False):
    """Start the distlockd server."""
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    server = LockServer(host, port)
    logging.info(f"Starting distlockd server on {host}:{port}")

    try:
        await server.start()
    except asyncio.CancelledError:
        logging.info("Server shutdown requested")
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        await server.stop()

def main():
    """Main entry point for the CLI."""
    args = parse_args()

    if args.command == 'server':
        try:
            asyncio.run(start_server(args.host, args.port, args.verbose))
        except KeyboardInterrupt:
            print("\nServer stopped by user")
        except Exception as e:
            print(f"Error: {e}")
            return 1
    else:
        print("No command specified. Use --help for usage.")
        return 1

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())