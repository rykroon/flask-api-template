from functools import wraps
from math import ceil
import time
from flask import g, request
from utils import Cache


class Throttle:
    def __init__(self, scope, rate):
        """
            :param scope: can be either 'anon' or 'user'
            :param rate: {num_requests}/{period} 
        """
        self.scope = scope
        self.num_of_requests, self.duration = self.parse_rate(rate)
        self.cache = Cache(key_prefix='throttle', timeout=self.duration)

    def get_cache_key(self):
        ident = None
        if self.scope == 'anon':
            ident = request.remote_addr or '127.0.0.1'

        if self.scope == 'user':
            if g.client:
                ident = g.client.pk

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

        history = self.cache.get(key, [])
        now = time.time()
        while history and history[-1] <= now - self.duration:
            history.pop()

        if len(history) >= self.num_of_requests:
            return False

        history.insert(0, now)
        self.cache.set(key, history, self.duration)
        return True

 