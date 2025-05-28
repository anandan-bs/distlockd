# distlockd

`distlockd` is a lightweight, zero-dependency distributed lock server implemented in Python. It enables multiple clients to coordinate access to shared resources using named locks over a simple TCP protocol. Built for simplicity, stability, and ease of integration, distlockd is ideal for teams who need distributed locking without the operational overhead of Redis or other heavyweight systems.

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
python -m distlockd.cli server

# Or, if installed as a package:
distlockd server

# With custom host and port
python -m distlockd.cli server --host 127.0.0.1 --port 9999
# Or
distlockd server --host 127.0.0.1 --port 9999

# Enable verbose logging
python -m distlockd.cli server -v
# Or
distlockd server -v
```

### Running the Benchmark

```bash
python -m distlockd.cli test distlockd|redis
# Or
distlockd test distlockd|redis

# With custom host and port
python -m distlockd.cli test distlockd|redis --host 127.0.0.1 --port 9999
# Or
distlockd test distlockd|redis --host 127.0.0.1 --port 9999

# With custom iterations, num_clients, num_locks, and throughput_seconds
python -m distlockd.cli test distlockd|redis --iterations 1000 --num_clients 1000 --num_locks 100 --throughput_seconds 10
# Or
distlockd test distlockd|redis --iterations 1000 --num_clients 1000 --num_locks 100 --throughput_seconds 10
```

### Client Examples

#### Basic Usage

```python
from distlockd.client import Client

# Create a client
client = Client() # default host: 127.0.0.1, port: 9999, specified host and port: Client(host="192.xx.xx.xx", port=9999)

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

- iterations: 1000
- num_clients: 1000
- num_locks: 100
- throughput_seconds: 10

### Methodology

- Both servers were tested using equivalent client logic and lock contention scenarios.
- Each test reports average, median, and worst-case latency, as well as throughput.
- Tests were run on the same hardware/network for fairness.

### Results (Summary)

- The following results were obtained using the configuration below:

  - **iterations:** 1000
  - **num_clients:** 1000
  - **num_locks:** 100
  - **throughput_seconds:** 10


  | Metric                       |                               distlockd                               |                                   Redis                                   |
  | ------------------------------ | :----------------------------------------------------------------------: | :-------------------------------------------------------------------------: |
  | Latency Min (ms)             |      0.07![Runner-up](https://img.shields.io/badge/Runner-up-red)      |  **0.05 🏆 ![Winner](https://img.shields.io/badge/Winner-brightgreen)**  |
  | Latency Max (ms)             | **1.01 🏆 ![Winner](https://img.shields.io/badge/Winner-brightgreen)** |       4.66![Runner-up](https://img.shields.io/badge/Runner-up-red)       |
  | Latency Avg (ms)             |      0.08![Runner-up](https://img.shields.io/badge/Runner-up-red)      |  **0.07 🏆 ![Winner](https://img.shields.io/badge/Winner-brightgreen)**  |
  | 95th Percentile (ms)         |      0.10![Runner-up](https://img.shields.io/badge/Runner-up-red)      |  **0.08 🏆 ![Winner](https://img.shields.io/badge/Winner-brightgreen)**  |
  | 99th Percentile (ms)         |      0.12![Runner-up](https://img.shields.io/badge/Runner-up-red)      |  **0.11 🏆 ![Winner](https://img.shields.io/badge/Winner-brightgreen)**  |
  | Throughput (ops/sec)         |    5200.00![Runner-up](https://img.shields.io/badge/Runner-up-red)    | **5710.00 🏆 ![Winner](https://img.shields.io/badge/Winner-brightgreen)** |
  | Concurrency Success Rate (%) |                               **100.00**                               |                                **100.00**                                |
- `distlockd` achieves sub-millisecond lock operations in most cases, with competitive or superior maximum latency compared to Redis. Throughput and concurrency success rates are robust even under heavy load.

## Acknowledgements

Thanks to [Windsurf](https://windsurf.ai/) for providing the benchmarking automation and comparison summary in this project.

## License

MIT
