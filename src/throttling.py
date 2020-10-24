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
        self.cache = Cache(key_prefix='throttle', timeout=self.duration)

    def get_cache_key(self):
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

    def allow_request(self):
        self.key = self.get_cache_key()
        self.history = self.cache.get(self.key, [])
        self.now = time.time()

        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_of_requests:
            return self.throttle_failure()

        return self.throttle_success()

    def throttle_success(self):
        self.history.insert(0, self.now)
        self.cache.set(self.key, self.history, self.duration)
        return True

    def throttle_failure(self):
        return False

    # def wait(self):
    #     if self.history:
    #         remaining_duration = self.duration - (self.now - self.history[-1])
    #     else:
    #         remaining_duration = self.duration

    #     available_requests = self.num_of_requests - len(self.history) + 1
    #     if available_requests <= 0:
    #         return None

    #     return remaining_duration / float(available_requests)
        