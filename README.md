# Mini-Redis 🚀

A lightweight, non-blocking, in-memory key-value data store built from scratch in pure Python. It implements the official Redis Serialization Protocol (RESP) and utilizes asynchronous I/O multiplexing, making it fully compatible with standard Redis clients.

## Features
* **Custom RESP Parser:** Communicates using standard RESP2, meaning you can connect to it using `redis-cli`, `redis-py`, or netcat.
* **Non-Blocking I/O:** Uses OS-level event notification (`epoll`/`kqueue` via Python's `selectors` module) to handle multiple concurrent client connections on a single thread.
* **LRU Eviction Policy:** Built-in Least Recently Used (LRU) cache management ensures the server never exceeds its predefined memory footprint (default limit: 1000 keys).
* **Passive TTL Expiration:** Supports key expiration natively (`EX` argument). Stale keys are dynamically evicted upon lookup to conserve CPU cycles.

## Supported Commands
* `PING` / `ECHO` - Connection health and debugging
* `SET key value [EX seconds]` - Store data with optional Time-To-Live
* `GET key` - Retrieve data
* `DEL key [key ...]` - Delete one or more keys
* `EXISTS key [key ...]` - Check key presence

## Quick Start

**1. Start the Server**
```bash
python server.py
