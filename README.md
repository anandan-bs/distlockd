# distlockd

`distlockd` is a lightweight, zero-dependency distributed lock server implemented in Python. It enables multiple clients to coordinate access to shared resources using named locks over a simple TCP protocol. Built for simplicity, stability, and ease of integration, distlockd is ideal for teams who need distributed locking without the operational overhead of Redis or other heavyweight systems.

## Requirements

- Python >= 3.6

## Installation

```bash
pip install distlockd
```

## Quick Start

```bash
# Start the server
distlockd server --host localhost --port 9001

# In your Python code
from distlockd.client import LockClient

client = LockClient('localhost', 9001)
with client.lock('my-resource'):
    # Your critical section here
    pass
```

## Architecture & Protocol

- **Server**: Asyncio-based TCP server, in-memory lock management, auto-timeout for stale locks (default: 10s), minimal resource usage.
- **Client**: Synchronous Python client, context manager support, unique client IDs, retry and timeout mechanisms.
- **Protocol**: Fast custom binary protocol inspired by RESP (used in Redis). This protocol minimizes parsing overhead and enables sub-millisecond lock operations, making it ideal for high-throughput, low-latency distributed coordination.
- **Design Philosophy**: Minimalism, reliability, and maintainability. No persistence, no external databases, no complex configuration.

## Features

- Named distributed locks (multiple resources, independent lock names)
- Simple TCP-based binary protocol
- Auto-timeout of stale locks (prevents deadlocks)
- Asyncio-based scalable server
- Synchronous, easy-to-use Python client
- Context-manager support for safe lock handling
- Health check endpoint for monitoring
- Configurable timeouts and retry logic
- No external dependencies (no Redis, no databases)
- Structured error handling and logging
- Lightweight and easy to deploy
- Connection pool for efficient connection management

## Installation

```bash
pip install distlockd
```

## Targeted Use Cases

- **Distributed cron jobs**: Ensure only one worker runs a scheduled task at a time across multiple hosts.
- **Leader election**: Elect a leader in a cluster for coordination tasks.
- **Resource coordination**: Prevent race conditions when accessing shared files, APIs, or other resources.
- **Testing and CI**: Synchronize test runners or deployment steps in distributed pipelines.
- **Lightweight alternatives to Redis locks**: When you want distributed locking but find Redis too heavy or complex.
- **Temporary critical sections**: Where lock persistence is not required and simplicity is key.

## Usage

### Starting the Server

```bash
# Basic usage (default host: 127.0.0.1, port: 9999)
distlockd server

# With custom host and port
distlockd server --host 127.0.0.1 --port 9999

# Enable verbose logging (Note: may impact performance in high-throughput scenarios)
distlockd server -v
```

### Running the Benchmark

```bash
distlockd test distlockd|redis

# With custom host and port
distlockd test distlockd|redis --host 127.0.0.1 --port 9999

# With custom iterations, num_clients, num_locks, and throughput_seconds
distlockd test distlockd|redis --iterations 1000 --num_clients 1000 --num_locks 100 --throughput_seconds 10
```

### Client Examples

#### Basic Usage

```python
from distlockd.client import Client

# Create a Basic client
client = Client() # default host: 127.0.0.1, port: 9999, specified host and port: Client(host="192.xx.xx.xx", port=9999)

# Create a Client with custom timeout and retry logic
client = Client(timeout=5.0, retry=3)

# Create a Client with verbose logging
client = Client(verbose=True)

# Check server health
if client.check_server_health():
    print("Server is healthy!")
```

#### Manual Lock Management

```python
# Manual lock acquisition and release
if client.acquire("my-resource", timeout=5.0):
    try:
        print("Lock acquired successfully")
        # Do critical work here...
    finally:
        if client.release("my-resource"):
            print("Lock released successfully")
```

#### Using Context Manager

```python
# Using context manager for automatic lock release
try:
    with client.lock("shared-resource", timeout=3.0):
        print("Lock acquired via context manager")
        # Do critical work here...
    # Lock is automatically released when the block exits
    print("Lock automatically released")
except Exception as e:
    print(f"Failed to acquire lock: {e}")
```

## Error Handling

Handle common exceptions:

```python
from distlockd.exceptions import LockAcquisitionTimeout, LockReleaseError, ConnectionError

try:
    with client.lock("resource"):
        # Critical section
        pass
except LockAcquisitionTimeout:
    print("Failed to acquire lock: timeout")
except LockReleaseError as e:
    print(f"Error releasing lock: {e}")
except ConnectionError as e:
    print(f"Connection error: {e}")
```

## Benchmark Comparison Report

**Date:** 2025-05-28 11:10:51

### System Info:

- Platform: Linux
- Platform-Release: 4.18.0-553.5.1.el8_10.x86_64
- Platform-Version: #1 SMP Tue May 21 03:13:04 EDT 2024
- Machine: x86_64
- Processor: x86_64
- CPU Count: 8
- RAM (GB): 15.39
- Uname:
  - system: Linux
  - release: 4.18.0-553.5.1.el8_10.x86_64
  - version: #1 SMP Tue May 21 03:13:04 EDT 2024
  - machine: x86_64
  - processor: x86_64

### Test Configuration:

- iterations: 1000 # for latency test
- num_clients: 100 # for concurrency test
- num_locks: 10 # for concurrency test
- throughput_seconds: 10 # for throughput test

### Methodology

- Both servers were tested using equivalent client logic and lock contention scenarios.
- Each test reports average, median, and worst-case latency, as well as throughput.
- Tests were run on the same hardware/network for fairness.

### 🥇 Metric-by-Metric Comparison

| Metric                    | Distlockd 🟦 | Redis 🔴 | 🏅 Winner |
|--------------------------|--------------|----------|-----------|
| **Latency Min (ms)**     | **0.22**     | 0.33     | 🏆 Distlockd |
| **Latency Max (ms)**     | **0.61**     | 0.86     | 🏆 Distlockd |
| **Latency Avg (ms)**     | **0.26**     | 0.39     | 🏆 Distlockd |
| **95th Percentile (ms)** | **0.34**     | 0.54     | 🏆 Distlockd |
| **99th Percentile (ms)** | **0.39**     | 0.63     | 🏆 Distlockd |
| **Throughput (ops/sec)** | **28540.00** | 5900.00  | 🏆 Distlockd |
| **Success Rate (%)**     | 100.00       | 100.00   | 🟰 Tie |

> ✅ **Distlockd** leads in all latency and throughput metrics
> 🤝 Both systems maintained a 100% success rate

---

### 🧠 Summary

- **Distlockd** outperforms **Redis** in every latency and throughput metric, with impressive **28.5k ops/sec**.
- Redis remains a solid baseline but is outpaced by Distlockd in high-concurrency locking.
- This makes **Distlockd** a top candidate for high-performance distributed coordination scenarios.

## Acknowledgements

Thanks to [Windsurf](https://windsurf.ai/) for providing the benchmarking automation and comparison summary in this project.

## License

MIT
