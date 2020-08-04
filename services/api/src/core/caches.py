from functools import wraps
import pickle
from flask import request
from db import redis_client


class Cache:

    def __init__(self, key_prefix=None, timeout=300):
        self.key_prefix = key_prefix
        self.default_timeout = timeout

    def __contains__(self, key):
        return self._prepend_key_prefix(key) in redis_client

    def get(self, key, default=None):
        value = redis_client.get(self._prepend_key_prefix(key))
        if value is None:
            return default
        return self._load_object(value)

    def set(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        value = self._dump_object(value)
        return redis_client.set(self._prepend_key_prefix(key), value, ex=timeout)

    def add(self, key, value, timeout=None):
        timeout = timeout or self.default_timeout
        value = self._dump_object(value)
        return redis_client.set(self._prepend_key_prefix(key), value, ex=timeout, nx=True)

    def delete(self, key):
        return redis_client.delete(self._prepend_key_prefix(key)) == 1

    def _dump_object(self, value):
        return pickle.dumps(value)

    def _load_object(self, value):
        if value is None:
            return None

        try:
            return pickle.loads(value)
        except pickle.UnpicklingError:
            return value

    def _prepend_key_prefix(self, key):
        if self.key_prefix:
            return '{}:{}'.format(self.key_prefix, key)
        return key


"""
    Article on on the concept of "Cacheable"
    https://developer.mozilla.org/en-US/docs/Glossary/Cacheable
"""

CACHEABLE_METHODS = ('GET', 'HEAD')
CACHEABLE_STATUS_CODES = (200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501)

def cache_page(seconds, key_prefix=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in CACHEABLE_METHODS:
                cache = Cache(timeout=seconds, key_prefix=key_prefix)
                response = cache.get(request.url)
                if response:
                    return response
                response = func(*args, **kwargs)
                if response.status_code in CACHEABLE_STATUS_CODES:
                    cache.set(request.url, response)
                return response
                
            return func(*args, **kwargs)
        return wrapper
    return decorator
