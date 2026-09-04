from collections import OrderedDict
import time


class RedisStore:

    def __init__(self, max_keys: int = 1000):
        self.max_keys = max_keys
        # OrderedDict gives us O(1) reads, updates, and LRU ordering
        self._data = OrderedDict()
        # Maps key -> epoch timestamp when it expires
        self._expiry = {}

    def set(
        self, key: str, value: str, ttl_seconds: int | None = None
    ) -> tuple[bool, str | None]:
        """Stores a key-value pair.

        Returns (True, evicted_key_or_None).
        """
        evicted_key = None

        # If key exists, refresh its position as most recently used
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value

        # Handle TTL deadline
        if ttl_seconds is not None:
            self._expiry[key] = time.time() + ttl_seconds
        elif key in self._expiry:
            del self._expiry[key]

        # Enforce LRU eviction if we exceed capacity
        if len(self._data) > self.max_keys:
            # popitem(last=False) pops the oldest/least recently used entry
            evicted_key, _ = self._data.popitem(last=False)
            if evicted_key in self._expiry:
                del self._expiry[evicted_key]

        return True, evicted_key

    def get(self, key: str) -> str | None:
        """Retrieves a key.

        Handles passive expiration and updates LRU position.
        """
        # 1. Check if key expired
        if key in self._expiry and time.time() > self._expiry[key]:
            self.delete(key)
            return None

        # 2. Check if key exists
        if key not in self._data:
            return None

        # 3. Mark as most recently used
        self._data.move_to_end(key)
        return self._data[key]

    def delete(self, key: str) -> int:
        deleted = 0
        if key in self._data:
            del self._data[key]
            deleted = 1
        if key in self._expiry:
            del self._expiry[key]
        return deleted

    def exists(self, key: str) -> int:
        return 1 if self.get(key) is not None else 0