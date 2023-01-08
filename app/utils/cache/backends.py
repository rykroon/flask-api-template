from utils.db import get_redis_client


class RedisBackend:

    serializer = None

    def __init__(self, client=None):
        self.client = client if client is not None else get_redis_client()

    def __getitem__(self, key):
        value = self.client.get(key)
        if value is None:
            raise KeyError(key)
        return self.serializer.loads(value)

    def __setitem__(self, key, value):
        ...

    def __delitem__(self, key):
        result = bool(self.client.delete(key))
        if not result:
            raise KeyError(key)

    def __contains__(self, key):
        return bool(self.client.exists(key))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key, ttl=None):
        ...

    def delete(self, key):
        try:
            del self[key]
            return True
        except KeyError:
            return False

    def exists(self, key):
        return key in self
