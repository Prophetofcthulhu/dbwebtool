"""
very much naive cache implementation
"""


class NaiveCache:
    def __init__(self):
        self._cache = {}

    def get(self, uuid):
        return self._cache.get(uuid)

    def put(self, uuid, obj):
        self._cache[uuid] = obj
