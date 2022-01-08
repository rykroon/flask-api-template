import os
from cachelib import RedisCache
from flask import Flask, g

from utils.db import get_redis_client
from utils.error_handlers import error_handlers
from utils.json import JSONEncoder
from utils.logging import get_logger
from views import bp as views_bp


def create_app():
    app = Flask(__name__)

    #json
    app.json_encoder = JSONEncoder

    #logger
    app.logger = get_logger()

    #redis
    app.config['REDIS_CLIENT'] = get_redis_client()

    #exception handlers
    for exc, handler in error_handlers.items():
        app.register_error_handler(exc, handler)

    #blueprints
    app.register_blueprint(views_bp)

    #before request
    @app.before_request
    def before_request():
        g.redis_client = app.config['REDIS_CLIENT']
        g.cache = RedisCache(host=g.redis_client)

    @app.route('/healthz', methods=['GET'])
    def health():
        return "OK"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)