import os

mongo_db = os.getenv('MONGO_DB')
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = os.getenv('MONGO_PORT', 27017)
#connect(mongo_db, host=mongo_host, port=mongo_port)

