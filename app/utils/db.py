import os

from flask import current_app, g, has_app_context, has_request_context
import redis


mongo_db = os.getenv('MONGO_DB')
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = os.getenv('MONGO_PORT', 27017)
#connect(mongo_db, host=mongo_host, port=mongo_port)


def get_redis_client():
    if has_request_context():
        return g.redis_client

    if has_app_context():
        return current_app.config['REDIS_CLIENT']

    return redis.StrictRedis(
        host=os.getenv('REDIS_HOST'),
        password=os.getenv('REDIS_PASSWORD'),
        db=0
    )
