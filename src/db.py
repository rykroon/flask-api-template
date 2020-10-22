import os
import redis

redis_host = os.getenv('REDIS_HOST')
redis_pass = os.getenv('REDIS_PASSWORD')
redis_connection_pool = redis.ConnectionPool(host=redis_host, password=redis_pass, db=0)

def get_redis_client():
    return redis.Redis(connection_pool=redis_connection_pool)
