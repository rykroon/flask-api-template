import os

from flask import current_app, g, has_app_context, has_request_context
from mongoengine import connect
import redis


def get_redis_client():
    if has_request_context():
        return g.redis_client

    if has_app_context():
        return current_app.config['REDIS_CLIENT']

    return redis.StrictRedis(
        host=os.getenv('REDIS_HOST'),
        password=os.getenv('REDIS_PASSWORD'),
        db=int(os.getenv('REDIS_DB', 0))
    )


def get_mongodb_client():

    if has_request_context():
        return g.mongodb_client

    if has_app_context():
        return current_app.config['MONGODB_CLIENT']

    username = os.getenv('MONGODB_USERNAME')
    password = os.getenv('MONGODB_PASSWORD')
    host = os.getenv('MONGODB_HOST')
    port = os.getenv('MONGODB_PORT', 27017)
    dbname = os.getenv('MONGODB_DBNAME', username)

    uri = 'mongodb://'
    if username and password:
        uri += f'{username}:{password}@'

    uri += f'{host}:{port}/{dbname}'
    return connect(host=uri)
