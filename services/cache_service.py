import time


class MemoryCache:

    def __init__(self):
        self._cache = {}

    def get(self, key):

        if key not in self._cache:
            return None

        value, expiry = self._cache[key]

        if time.time() > expiry:
            del self._cache[key]
            return None

        return value

    def set(self, key, value, ttl):

        self._cache[key] = (
            value,
            time.time() + ttl
        )

    def clear(self):
        self._cache.clear()


cache = MemoryCache()