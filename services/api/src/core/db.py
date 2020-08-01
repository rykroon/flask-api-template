import os
from mongoengine import connect
from redis import Redis


mongo_host = os.getenv('MONGODB_HOST')
connect('test_db', host=mongo_host)

redis_host = os.getenv('REDIS_HOST')
redis_pass = os.getenv('REDIS_PASSWORD')
redis0 = Redis(host=redis_host, password=redis_pass, db=0)
