from functools import wraps
import pickle
from flask import request
from db import redis_client


class Cache:

    def __init__(self, key_prefix=None, default_timeout=300):
        self.default_timeout = default_timeout
        self.key_prefix = key_prefix

    def __contains__(self, key):
        return key in redis_client

    def get(self, key, default=None):
        value = redis_client.get(key)
        if value is None:
            return default
        return self._load_object(value)

    def set(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        value = self._dump_object(value)
        return redis_client.set(key, value, ex=timeout)

    def add(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        value = self._dump_object(value)
        return redis_client.set(key, value, ex=timeout, nx=True)

    def delete(self, key):
        return redis_client.delete(key) == 1

    def _dump_object(self, value):
        return pickle.dumps(value)

    def _load_object(self, value):
        if value is None:
            return None

        try:
            return pickle.loads(value)
        except pickle.UnpicklingError:
            return value


def cache(seconds):
    cache = Cache(default_timeout=seconds)
    def decorator(func):
        @wraps
        def wrapper(*args, **kwargs):
            if request.method == 'GET':
                pass
                #cache logic
            return func(*args, **kwargs)
        return wrapper
    return decorator
