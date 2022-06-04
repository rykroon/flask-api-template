from utils.cache.backends import RedisBackend


DEFAULT = object()


def default_key_builder(key, ns=None):
    if ns is None:
        return key
    return f"{ns}:{key}"


class Cache:

    default_ttl = 300

    def __init__(self, namespace=None, ttl=DEFAULT, key_builder=None):
        self.backend = RedisBackend()
        self.namespace = namespace
        self.default_ttl = self.default_ttl if ttl is DEFAULT else ttl
        self.key_builder = default_key_builder if key_builder is None else key_builder

    def get(self, key, default=None):
        key = self.key_builder(key, self.namespace)
        return self.backend.get(key, default=default)

    def set(self, key, value, ttl=DEFAULT):
        key = self.key_builder(key, self.namespace)
        ttl = self.default_ttl if ttl is DEFAULT else ttl
        return self.backend.set(key, value, ttl)

    def delete(self, key):
        key = self.key_builder(key, self.namespace)
        return self.backend.delete(key)

    def exists(self, key):
        key = self.key_builder(key, self.namespace)
        return self.backend.exists(key)

