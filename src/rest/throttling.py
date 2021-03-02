from functools import wraps
from math import ceil
import time
from flask import current_app, g, request
from utils import Cache


class BaseThrottle:
    def allow_request(self):
        raise NotImplementedError

    def get_ident(self):
        if request.access_route:
            return ','.join(request.access_route)
        return request.remote_addr or '127.0.0.1'

    def wait(self):
        raise NotImplementedError


class MovingWindowThrottle(BaseThrottle):
    scope = None
    rate = None

    def __init__(self, scope=None, rate=None):
        if scope:
            self.scope = scope

        if rate:
            self.rate = rate

        self.num_of_requests, self.duration = self.parse_rate(self.rate)
        self.cache = Cache(key_prefix='throttle', timeout=self.duration)

    def get_cache_key(self):
        """
            concatenates the scope and the identifier
        """
        ident = self.get_ident()
        if ident is not None:
            return '{}:{}'.format(self.scope, ident)

    def parse_rate(self, rate):
        num_requests, _, period = rate.partition('/')
        num_requests = int(num_requests)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)

    def allow_request(self):
        key = self.get_cache_key()
        if key is None:
            return True

        self.history = self.cache.get(key, [])
        self.now = time.time()
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_of_requests:
            return False

        self.history.insert(0, self.now)
        self.cache.set(key, self.history, self.duration)
        return True

    def wait(self):
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_of_requests - len(self.history) + 1
        if available_requests <= 0:
            return None

        return remaining_duration / float(available_requests)


class AnonThrottle(MovingWindowThrottle):
    scope = 'anon'
    rate = '6/minute'

    def get_ident(self):
        if g.client is not None:
            #return None if the request is authenticated.
            return None
        return super().get_ident()


class ClientThrottle(MovingWindowThrottle):
    scope = 'client'
    rate = '1000/hour'

    def get_ident(self):
        if g.client:
            return g.client.pk
        #if the request is not authenticated full back to the ip address.
        return super().get_ident()


class BurstThrottle(ClientThrottle):
    scope = 'burst'
    rate = '60/minute'


class SustainedThrottle(ClientThrottle):
    scope = 'sustained'
    rate = '10000/day'