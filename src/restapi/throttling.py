from functools import wraps
from math import ceil
import time
from flask import g, request
from werkzeug.exceptions import TooManyRequests
from cache import Cache


def throttle(scope, rate):  
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            throttler = Throttler(scope, rate)
            throttler.throttle()
            return func(*args, **kwargs)
        return wrapper
    return decorator


class Throttler:
    def __init__(self, scope, rate):
        self.scope = scope
        self.num_of_requests, self.duration = self.parse_rate(rate)
        self.cache = Cache(key_prefix='throttle', timeout=self.duration)

    @property
    def key(self):
        if 'user' in g:
            ident = g.user
        else:
            ident = request.remote_addr

        return '{}:{}'.format(self.scope, ident)

    def parse_rate(self, rate):
        num, _, period = rate.partition('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)

    def throttle(self):
        history = self.cache.get(self.key, [])
        now = time.time()
        while history and history[-1] <= now - self.duration:
            history.pop()

        if len(history) >= self.num_of_requests:
            retry_after = ceil(self.duration - (now - history[-1]))
            raise TooManyRequests(retry_after=retry_after)

        history.insert(0, now)
        self.cache.set(self.key, history, self.duration)
        return True

 