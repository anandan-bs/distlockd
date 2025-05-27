# distlockd

`distlockd` is a lightweight, zero-dependency distributed lock server implemented in Python. It enables multiple clients to coordinate access to shared resources using named locks over a simple TCP protocol. Built for simplicity, stability, and ease of integration, distlockd is ideal for teams who need distributed locking without the operational overhead of Redis or other heavyweight systems.

## Architecture & Protocol

- **Server**: Asyncio-based TCP server, in-memory lock management, auto-timeout for stale locks (default: 10s), minimal resource usage.
- **Client**: Synchronous Python client, context manager support, unique client IDs, retry and timeout mechanisms.
- **Protocol**: Simple binary line protocol (`LOCK`, `RELEASE`, `HEALTH`), no external dependencies, easy to implement in any language.
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
# Basic usage (default host: 0.0.0.0, port: 8888)
python -m distlockd server

# With custom host and port
python -m distlockd server --host 127.0.0.1 --port 9999

# Enable verbose logging
python -m distlockd server -v
```

### Client Examples

#### Basic Usage

```python
from distlockd import Client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a client
client = Client(host='localhost', port=8888)

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

## Benchmarks

Performance tests compare `distlockd` against Redis-based distributed locks under various loads and concurrency levels. The benchmarks measure:

- **Lock acquisition/release latency**
- **Throughput (locks/sec)**
- **Concurrency handling**

### Methodology
- Both servers were tested using equivalent client logic and lock contention scenarios.
- Each test reports average, median, and worst-case latency, as well as throughput.
- Tests were run on the same hardware/network for fairness.

### Results (Summary)
- `distlockd` demonstrates competitive or superior latency compared to Redis for basic distributed locking workloads, with very low overhead.
- For most use cases, lock acquisition and release are sub-millisecond.
- Throughput scales well with moderate concurrency, making it suitable for most coordination tasks.

See the full interactive benchmark report by opening the following file in your web browser after running the benchmarks:

`benchmarks/benchmark_report.html`

> **Note:**
> GitHub does not render local HTML files. To view the interactive report, clone the repository and open the file above in your browser. Here is the report:

### 📈 Benchmark Highlights

| Test Type      | Metric                 | Result         |
|----------------|------------------------|---------------|
| **Latency**    | Minimum                | **0.00 ms**   |
|                | Maximum                | **6.00 ms**   |
|                | Average                | **0.41 ms**   |
|                | 95th Percentile        | **1.01 ms**   |
|                | 99th Percentile        | **1.14 ms**   |
| **Throughput** | Average Ops/sec        | **971**       |
| **Concurrency**| Clients                | **100**       |
|                | Locks                  | **10**        |
|                | Success Rate           | **100%**      |

> **Summary:**
> - Lock operations are consistently fast, with average latency well below 1 ms.
> - The server handles nearly 1,000 lock/unlock operations per second.
> - In a high-concurrency scenario (100 clients, 10 locks), all operations succeeded.


## License

MIT
