from functools import wraps
import time
from cache import Cache
    
def throttle(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = Cache(key_prefix='throttle')
        history = cache.get('', [])
        now = time.time()



        
        return func(*args, **kwargs)
    return wrapper

    
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