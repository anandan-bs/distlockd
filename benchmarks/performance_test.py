"""
Performance testing script for distlockd.
Measures latency, throughput, and concurrency handling.
"""
import time
import logging
import threading
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from queue import Queue

# Add the parent directory to sys.path to import distlockd
sys.path.insert(0, str(Path(__file__).parent.parent))

from distlockd.client import Client
from distlockd.constants import (
    DEFAULT_HOST,
    DEFAULT_PORT
)

# HTML template for the report
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>distlockd Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{ background-color: #f8f9fa; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metric {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .metric h3 {{ margin-top: 0; color: #2c3e50; }}
        .error {{ color: #e74c3c; }}
        .success {{ color: #27ae60; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>distlockd Performance Report</h1>
        <p>Generated on: {timestamp}</p>
        {content}
    </div>
</body>
</html>'''

class PerformanceTester:

    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.results: Dict[str, Any] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        # Create a stream handler
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def measure_latency(self, iterations=1000):
        """Measure lock acquisition and release latency."""
        client = Client(self.host, self.port)
        latencies = []

        for i in range(iterations):
            start = time.time()
            try:
                if client.acquire(f"test-lock-{i}", timeout=0.5):
                    latency = (time.time() - start) * 1000  # Convert to ms
                    latencies.append(latency)
                    # Release the lock with the same name
                    client.release(f"test-lock-{i}")
            except Exception as e:
                self.logger.error(f"Error in iteration {i}: {e}")
                continue

        if not latencies:
            raise RuntimeError("No successful operations recorded")

        return {
            'min': min(latencies),
            'max': max(latencies),
            'avg': statistics.mean(latencies),
            'p95': statistics.quantiles(latencies, n=20)[18],  # 95th percentile
            'p99': statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        }

    def measure_throughput(self, duration=10, num_threads=10):
        """Measure operations per second using multiple threads."""
        stop_event = threading.Event()
        ops_queue = Queue()

        def worker():
            client = Client(self.host, self.port)
            ops = 0
            lock_name = f"test-lock-{threading.get_ident()}"
            while not stop_event.is_set():
                try:
                    # Acquire and release in a loop
                    for _ in range(100):
                        if client.acquire(lock_name, timeout=0.5):
                            client.release(lock_name)
                            ops += 1
                except Exception as e:
                    self.logger.error(f"Error in worker: {e}")
                    continue
            ops_queue.put(ops)

        # Start worker threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)

        # Let them run for specified duration
        time.sleep(duration)
        stop_event.set()

        # Collect results
        total_ops = 0
        for _ in range(num_threads):
            total_ops += ops_queue.get()

        for t in threads:
            t.join()

        return total_ops / duration

    def test_concurrent_clients(self, num_clients=100, num_locks=10):
        """Test behavior with multiple concurrent clients using thread pool."""
        def client_worker(args):
            client_id, lock_name = args
            client = Client(self.host, self.port)
            try:
                with client.lock(lock_name, timeout=5.0):
                    time.sleep(0.1)  # Simulate work
                return True
            except Exception:
                return False

        # Create work items
        work_items = [
            (i, f"concurrent-lock-{i % num_locks}")
            for i in range(num_clients)
        ]

        # Use thread pool to run concurrent clients
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            results = list(executor.map(client_worker, work_items))

        success_rate = sum(results) / len(results) * 100
        return success_rate

    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML report from test results."""
        content = []

        # Latency Section
        content.append("""
            <h2>Latency Test Results</h2>
            <div class="metric">
                <h3>Lock Operation Latency (milliseconds)</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value (ms)</th>
                    </tr>
                    <tr><td>Minimum</td><td>{:.2f}</td></tr>
                    <tr><td>Maximum</td><td>{:.2f}</td></tr>
                    <tr><td>Average</td><td>{:.2f}</td></tr>
                    <tr><td>95th Percentile</td><td>{:.2f}</td></tr>
                    <tr><td>99th Percentile</td><td>{:.2f}</td></tr>
                </table>
            </div>
        """.format(
            results['latency']['min'],
            results['latency']['max'],
            results['latency']['avg'],
            results['latency']['p95'],
            results['latency']['p99']
        ))

        # Throughput Section
        content.append("""
            <h2>Throughput Test Results</h2>
            <div class="metric">
                <h3>Operations Per Second</h3>
                <p>Average: <strong>{:.2f} ops/sec</strong></p>
            </div>
        """.format(results['throughput']))

        # Concurrency Section
        content.append("""
            <h2>Concurrency Test Results</h2>
            <div class="metric">
                <h3>Multiple Client Success Rate</h3>
                <p>Success Rate: <strong>{:.2f}%</strong></p>
            </div>
        """.format(results['concurrency']))

        return HTML_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            content="\n".join(content)
        )

def main():
    tester = PerformanceTester()
    results = {}

    print("Running latency tests...")
    results['latency'] = tester.measure_latency()

    print("Running throughput tests...")
    results['throughput'] = tester.measure_throughput()

    print("Running concurrency tests...")
    results['concurrency'] = tester.test_concurrent_clients()

    # Generate and save report
    report = tester.generate_html_report(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = Path.home() / f"performance_report_{timestamp}.html"

    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\nPerformance testing complete. Report saved to {report_file}")

if __name__ == '__main__':
    main()
