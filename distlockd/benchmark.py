"""
Unified benchmarking script for distlockd and Redis.
Usage:
    python benchmark.py --backend redis --host localhost --port 6379 [options]
    python benchmark.py --backend distlockd --host localhost --port 9999 [options]

This script can be imported and called from the CLI.
"""
import time
import logging
import threading
import statistics

import sys
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

try:
    import redis
except ImportError:
    redis = None

try:
    from .client import Client as DistlockdClient
except ImportError:
    DistlockdClient = None

class BenchmarkRunner:
    def __init__(self, backend, host, port, iterations=1000, num_clients=100, num_locks=10, throughput_seconds=10, verbose=False):
        """
        Initialize the benchmark runner.

        Args:
            backend (str): The backend to use (distlockd or redis).
            host (str): The hostname or IP address of the server.
            port (int): The port number to use.
            iterations (int): The number of iterations to run.
            num_clients (int): The number of clients to run.
            num_locks (int): The number of locks to test.
            throughput_seconds (int): The number of seconds to run the throughput test.
            verbose (bool): Whether to print verbose logging.
        """
        self.backend = backend
        self.host = host
        self.port = port
        self.iterations = iterations
        self.num_clients = num_clients
        self.num_locks = num_locks
        self.throughput_seconds = throughput_seconds
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        if not self.logger.hasHandlers():
            self.logger.addHandler(handler)

        if backend == 'redis' and not redis:
            self.logger.error('redis-py is not installed')
            sys.exit(1)
        if backend == 'distlockd' and not DistlockdClient:
            self.logger.error('distlockd is not installed or not importable')
            sys.exit(1)

        try:
            _ = self._get_client()
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.backend} server at {self.host}:{self.port}: {e}")
            sys.exit(1)

    def _get_client(self):
        """
        Get a client object for the specified backend.
        """
        if self.backend == 'redis':
            client = redis.Redis(host=self.host, port=self.port)
            if not client.ping():
                raise ConnectionError(f"Failed to connect to Redis server at {self.host}:{self.port}")
            return client
        elif self.backend == 'distlockd':
            client = DistlockdClient(self.host, self.port, verbose=self.verbose)
            if not client.check_server_health():
                raise ConnectionError(f"Failed to connect to distlockd server at {self.host}:{self.port}")
            return client
        else:
            self.logger.error('Unknown backend')
            sys.exit(1)

    def measure_latency(self):
        """
        Measure the latency of the specified backend.
        """
        latencies = []
        for i in range(self.iterations):
            lock_name = f"test-lock-{i}"
            start = time.time()
            try:
                if self.backend == 'redis':
                    client = self._get_client()
                    lock = client.lock(lock_name, timeout=10)
                    acquired = lock.acquire(blocking=True, blocking_timeout=0.5)
                    if acquired:
                        latency = (time.time() - start) * 1000
                        latencies.append(latency)
                        lock.release()
                else:
                    client = self._get_client()
                    acquired = client.acquire(lock_name, timeout=0.5)
                    if acquired:
                        latency = (time.time() - start) * 1000
                        latencies.append(latency)
                        client.release(lock_name)
            except Exception as e:
                self.logger.error(f"Error in iteration {i}: {e}")
                continue
        if not latencies:
            self.logger.error("No successful operations recorded")
            sys.exit(1)
        return {
            'min': min(latencies),
            'max': max(latencies),
            'avg': statistics.mean(latencies),
            'p95': statistics.quantiles(sorted(latencies), n=20)[-1],
            'p99': statistics.quantiles(sorted(latencies), n=100)[-1],
        }

    def measure_throughput(self):
        """
        Measure the throughput of the specified backend.
        """
        stop_event = threading.Event()
        ops_queue = Queue()
        def worker():
            client = self._get_client()
            ops = 0
            lock_name = f"test-lock-{threading.get_ident()}"
            if self.backend == 'redis':
                lock = client.lock(lock_name, timeout=10)
            while not stop_event.is_set():
                try:
                    for _ in range(100):
                        if self.backend == 'redis':
                            acquired = lock.acquire(blocking=True, blocking_timeout=0.5)
                            if acquired:
                                lock.release()
                                ops += 1
                        else:
                            acquired = client.acquire(lock_name, timeout=0.5)
                            if acquired:
                                client.release(lock_name)
                                ops += 1
                except Exception as e:
                    self.logger.error(f"Error in worker: {e}")
                    continue
            ops_queue.put(ops)
        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)
        time.sleep(self.throughput_seconds)
        stop_event.set()
        total_ops = 0
        for _ in range(10):
            total_ops += ops_queue.get()
        for t in threads:
            t.join()
        return total_ops / self.throughput_seconds

    def test_concurrent_clients(self):
        """
        Test the concurrency of the specified backend.
        """
        def client_worker(args):
            _, lock_name = args
            try:
                if self.backend == 'redis':
                    client = self._get_client()
                    lock = client.lock(lock_name, timeout=10)
                    acquired = lock.acquire(blocking=True, blocking_timeout=5.0)
                    if acquired:
                        time.sleep(0.1)
                        lock.release()
                        return True
                    return False
                else:
                    client = self._get_client()
                    with client.lock(lock_name, timeout=5.0):
                        time.sleep(0.1)
                    return True
            except Exception:
                return False
        work_items = [
            (i, f"concurrent-lock-{i % self.num_locks}")
            for i in range(self.num_clients)
        ]
        with ThreadPoolExecutor(max_workers=self.num_clients) as executor:
            results = list(executor.map(client_worker, work_items))
        success_rate = (sum(results) / len(results)) * 100
        return success_rate

    def run_all(self):
        """
        Run all of the benchmarks.
        """
        print(f"Running {self.backend} benchmark on {self.host}:{self.port}")
        latency = self.measure_latency()
        print("Latency test completed")
        throughput = self.measure_throughput()
        print("Throughput test completed")
        concurrency = self.test_concurrent_clients()
        print("Concurrency test completed")
        results = {
            'latency': latency,
            'throughput': throughput,
            'concurrency': concurrency
        }
        self.print_results(results)

    def print_results(self, results):
        print(f"\n# {self.backend.capitalize()} Benchmark Results\n")
        print("\n# Test Parameters\n")
        print(f"Iterations: {self.iterations}")
        print(f"Number of clients: {self.num_clients}")
        print(f"Number of locks: {self.num_locks}")
        print(f"Throughput seconds: {self.throughput_seconds}")
        print("\n# Results\n")

        print("| Metric | Value |")
        print("|--------|-------|")
        latency = results['latency']
        print(f"| Latency Min (ms) | {latency['min']:.2f} |")
        print(f"| Latency Max (ms) | {latency['max']:.2f} |")
        print(f"| Latency Avg (ms) | {latency['avg']:.2f} |")
        print(f"| 95th Percentile (ms) | {latency['p95']:.2f} |")
        print(f"| 99th Percentile (ms) | {latency['p99']:.2f} |")
        print(f"| Throughput (ops/sec) | {results['throughput']:.2f} |")
        print(f"| Concurrency Success Rate (%) | {results['concurrency']:.2f} |")
