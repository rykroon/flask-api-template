from functools import wraps
import pickle
from flask import request
from db import redis_client


class Cache:

    def __init__(self, key_prefix=None, timeout=300):
        self.key_prefix = key_prefix
        self.default_timeout = timeout

    def __contains__(self, key):
        return self._get_key(key) in redis_client

    def get(self, key, default=None):
        value = redis_client.get(self._get_key(key))
        if value is None:
            return default
        return self._load_object(value)

    def set(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        value = self._dump_object(value)
        return redis_client.set(self._get_key(key), value, ex=timeout)

    def add(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        value = self._dump_object(value)
        return redis_client.set(self._get_key(key), value, ex=timeout, nx=True)

    def delete(self, key):
        return redis_client.delete(self._get_key(key)) == 1

    def _dump_object(self, value):
        return pickle.dumps(value)

    def _load_object(self, value):
        if value is None:
            return None

        try:
            return pickle.loads(value)
        except pickle.UnpicklingError:
            return value

    def _get_key(self, key):
        if self.key_prefix:
            return '{}:{}'.format(self.key_prefix, key)
        return key


def cache_page(seconds, key_prefix=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in ('GET', 'HEAD'):
                cache = Cache(timeout=seconds, key_prefix=key_prefix)
                response = cache.get(request.url)
                if response:
                    return response
                response = func(*args, **kwargs)
                if response.status_code == 200:
                    cache.set(request.url, response)
                return response
                
            return func(*args, **kwargs)
        return wrapper
    return decorator
