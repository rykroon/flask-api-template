from functools import wraps
import time
from flask import g, request
from werkzeug.exceptions import TooManyRequests
from cache import Cache


def throttle(scope, rate):  
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            throttle = Throttle(scope, rate)
            if not throttle.allow_request():
                raise TooManyRequests

            return func(*args, **kwargs)
        return wrapper
    return decorator


class Throttle:
    def __init__(self, scope, rate):
        self.scope = scope
        self.num_of_requests, self.duration = self.parse_rate(rate)

    def parse_rate(self, rate):
        num_of_requests, period = rate.partition('/')
        num_of_requests = int(num_of_requests)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_of_requests, duration)

    def get_cache_key(self):
        if 'jwt_payload' in g:
            ident = g.jwt_payload.get('sub')
        else:
            ident = request.remote_addr

        return '{}:{}'.format(self.scope, ident)

    def allow_request(self):
        cache = Cache(key_prefix='throttle', timeout=self.duration)
        key = self.get_cache_key()
        history = cache.get(key, [])
        now = time.time()

        while history and history[-1] <= now - self.duration:
            history.pop()

        if len(history) >= self.num_of_requests:
            return False

        history.insert(0, now)
        cache.set(key, history, self.duration)
        return True
        