from functools import wraps
import pickle

from flask import g, request

from utils.db import get_redis_client

# use 'Undefined' to differentiate between 'None' and 
# the absense of passing in a value.
Undefined = object()


class Cache:
    def __init__(self, key_prefix=None, timeout=Undefined):
        self.key_prefix = key_prefix
        self.default_timeout = 300 if timeout is Undefined else timeout
        self._client = get_redis_client()

    def __contains__(self, key):
        key = self._make_key(key)
        return key in self._client

    def get(self, key, default=None):
        key = self._make_key(key)
        value = self._client.get(key)
        if value is None:
            return default
        
        try:
            return pickle.loads(value)
        except pickle.UnpicklingError:
            return value

    def set(self, key, value, timeout=Undefined):
        key = self._make_key(key)
        value = pickle.dumps(value)
        timeout = self.default_timeout if timeout is Undefined else timeout
        return self._client.set(key, value, ex=timeout)

    def touch(self, key, timeout=Undefined):
        key = self._make_key(key)
        timeout = self.default_timeout if timeout is Undefined else timeout
        return self._client.expire(key, timeout)

    def delete(self, key):
        key = self._make_key(key)
        return self._client.delete(key) == 1

    def _make_key(self, key):
        if self.key_prefix:
            return '{}:{}'.format(self.key_prefix, key)
        return key


def cache_page(timeout, key_prefix=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in ('GET', 'HEAD'):
                cache = Cache(key_prefix=key_prefix, timeout=timeout)
                key = '{}:{}'.format(g.client.pk, request.full_path)
                resp = cache.get(key)
                if not resp:
                    resp = func(*args, **kwargs)
                    if resp.status_code == 200:
                        cache.set(key, resp)
                return resp
            return func(*args, **kwargs)
        return wrapper
    return decorator

