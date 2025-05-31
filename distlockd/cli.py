"""
Command-line interface for distlockd server.

This module provides the command-line interface for running and managing the distlockd server.
It handles server startup, configuration, and graceful shutdown via signal handling.

Requirements:
    Python >= 3.6

Example:
    To start the server:
        $ distlockd server --host localhost --port 9001
"""
import argparse
import asyncio
import sys
import signal

from .server import main as server_main
from .constants import DEFAULT_HOST, DEFAULT_PORT
from .benchmark import BenchmarkRunner

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='distlockd - A lightweight distributed lock server')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Server command
    server_parser = subparsers.add_parser('server', help='Start the distlockd server')
    server_parser.add_argument(
        '--host',
        type=str,
        default=DEFAULT_HOST,
        help='Host to bind the server to (default: {})'.format(DEFAULT_HOST)
    )
    server_parser.add_argument(
        '-p', '--port',
        type=int,
        default=DEFAULT_PORT,
        help='Port to listen on (default: {})'.format(DEFAULT_PORT)
    )
    server_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    # Benchmark/test command
    test_parser = subparsers.add_parser('test', help='Run distlockd/redis benchmarks')
    test_parser.add_argument('backend', choices=['redis', 'distlockd'], help='Which backend to test')
    test_parser.add_argument('--host', type=str, help='Host to connect to')
    test_parser.add_argument('--port', type=int, help='Port to connect to')
    test_parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations for latency test')
    test_parser.add_argument('--num-clients', type=int, default=100, help='Number of clients for concurrency test')
    test_parser.add_argument('--num-locks', type=int, default=10, help='Number of locks for concurrency test')
    test_parser.add_argument('--throughput-seconds', type=int, default=10, help='Seconds for throughput test')
    test_parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    return parser.parse_args()

def main():
    """Main entry point for the CLI."""
    args = parse_args()

    if args.command == 'server':
        try:
            print(f"distlockd version: {__import__('distlockd').__version__}")

            # Set up signal handlers for graceful shutdown
            def handle_signal(signum, _):
                print(f"Received signal {signal.Signals(signum).name}")
                # This will raise a KeyboardInterrupt
                raise KeyboardInterrupt

            signal.signal(signal.SIGINT, handle_signal)
            signal.signal(signal.SIGTERM, handle_signal)

            # Run the server
            asyncio.run(server_main(args.host, args.port, verbose=args.verbose))
        except KeyboardInterrupt:
            print("Server stopped by user")
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
    elif args.command == 'test':
        host = args.host or "localhost"
        port = args.port or 6379 if args.backend == 'redis' else 9999
        bench_args = {
            'iterations': args.iterations,
            'num_clients': args.num_clients,
            'num_locks': args.num_locks,
            'throughput_seconds': args.throughput_seconds,
            'verbose': args.verbose
        }
        runner = BenchmarkRunner(args.backend, host, port, **bench_args)
        runner.run_all()
        return 0
    else:
        print("No command specified. Use --help for usage.")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())