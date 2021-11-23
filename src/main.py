import os
from cachelib import RedisCache
from flask import Flask, g
import redis
from flaskauth import AuthenticationMiddleware, BasicAuthentication
from utils.cache import get_redis_client
from utils import JSONEncoder, error_handlers
#from views import blueprints


def create_app():
    app = Flask(__name__)

    #json
    app.json_encoder = JSONEncoder

    #redis
    app.config['REDIS_CLIENT'] = get_redis_client()

    #exception handlers
    for exc, handler in error_handlers.items():
        app.register_error_handler(exc, handler)

    #blueprints
    # for bp in blueprints:
    #     app.register_blueprint(bp)

    #before request
    @app.before_request
    def redis_connection():
        g.redis_client = app.config['REDIS_CLIENT']
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