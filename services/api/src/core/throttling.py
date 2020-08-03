from functools import wraps
import time
from flask import abort, g, request
from caches import Cache


class BaseThrottle:
    def __init__(self, key_func, rate, scope=None):
        self.key_func = key_func
        self.num_requests, self.duration = self._parse_rate(rate)
        self.scope = scope
        if self.scope:
            key_prefix = 'throttle:{}'.format(self.scope)
        else:
            key_prefix = 'throttle'

        self.cache = Cache(key_prefix=key_prefix, timeout=self.duration)
        self.history = self.cache.get(self.key_func(), [])

    def allow_request(self):
        raise NotImplementedError

    def _parse_rate(self, rate):
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        """
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)


class Throttle(BaseThrottle):
    """
        A rate limiting class that uses the sliding window algorithm
    """
    def allow_request(self):
        start_of_window = time.time() - self.duration
        while self.history and self.history[-1] < start_of_window:
            self.history.pop()

        if len(self.history) > self.num_requests:
            return False

        self.history.insert(0, time.time())
        self.cache.set(self.key_func(), self.history, timeout=self.duration)
        return True


def get_remote_addr():
    # might need to check X-Forwarded-For header
    return request.remote_addr


def get_user():
    if 'user' in g:
        return g.user.pk
    return None


def throttle(key_func, rate, scope=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            throttle = Throttle(key_func=key_func, rate=rate, scope=scope)
            if not throttle.allow_request():
                abort(429)
            return func(*args, **kwargs)
        return wrapper
    return decorator

