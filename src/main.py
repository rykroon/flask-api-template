import os
from cachelib import RedisCache
from flask import Flask, current_app, g
import redis
from flaskauth import AuthenticationMiddleware, BasicAuthentication
from utils import JSONEncoder, error_handlers
#from views import blueprints


def create_app():
    app = Flask(__name__)

    #json
    app.json_encoder = JSONEncoder

    #redis
    redis_host = os.getenv('REDIS_HOST')
    redis_pass = os.getenv('REDIS_PASSWORD')
    app.config['REDIS_CONNECTION_POOL'] = redis.ConnectionPool(
        host=redis_host, 
        password=redis_pass, 
        db=0
    )

    #exception handlers
    for exc, handler in error_handlers.items():
        app.register_error_handler(exc, handler)

    #blueprints
    # for bp in blueprints:
    #     app.register_blueprint(bp)

    #before request
    @app.before_request
    def redis_connection():
        g.redis_client = redis.Redis(
            connection_pool=app.config['REDIS_CONNECTION_POOL']
        )
        g.cache = RedisCache(host=g.redis_client)

    @app.before_request
    def auth_middleware():
        AuthenticationMiddleware(
            authentication_classes=[
                BasicAuthentication
            ]
        )()

    @app.route('/healthz', methods=['GET'])
    def health():
        return "OK"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)