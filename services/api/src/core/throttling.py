import os
import time
from flask import abort, g, request
from caches import Cache


class BaseThrottle:
    """
        Rate throttling of requests.
    """

    def allow_request(self):
        """
            Return `True` if the request should be allowed, `False` otherwise.
        """
        raise NotImplementedError('.allow_request() must be overridden')

    def wait(self):
        """
            Optionally, return a recommended number of seconds to wait before
            the next request.
        """
        return None


class Throttle(BaseThrottle):

    cache = Cache(key_prefix='throttle')
    rate = os.getenv('THROTTLE_RATE')
    scope = None
    timer = time.time

    def __init__(self, rate=None, scope=None):
        if rate:
            self.rate = rate

        if scope:
            self.scope = scope

        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self):
        if g.user and g.user.is_authenticated:
            ident = g.user.pk
        else:
            ident = request.remote_addr

        return '{scope}_{ident}'.format(scope=self.scope, ident=ident)

    def parse_rate(self, rate):
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

    def allow_request(self):
        """
            Implement the check to see if the request should be throttled.
            On success calls `throttle_success`.
            On failure calls `throttle_failure`.
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key()
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
            
        return self.throttle_success()

    def throttle_success(self):
        """
            Inserts the current request's timestamp along with the key
            into the cache.
        """
        self.history.insert(0, self.now)
        self.cache.set(self.key, self.history, self.duration)
        return True

    def throttle_failure(self):
        """
            Called when a request to the API has failed due to throttling.
        """
        return False

    def wait(self):
        """
        Returns the recommended next request time in seconds.
        """
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return None

        return remaining_duration / float(available_requests)


def get_remote_addr():
    # might need to check X-Forwarded-For header
    return request.remote_addr


def get_user():
    return g.user.pk

