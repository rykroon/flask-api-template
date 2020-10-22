from flask import Flask, g, jsonify
from werkzeug.exceptions import HTTPException
from utils import JSONEncoder
from db import get_redis_client


def create_app():
    app = Flask(__name__)
    app.json_encoder = JSONEncoder

    @app.errorhandler(HTTPException)
    def http_exception_handler(e):
        return jsonify(
            error=e.name,
            error_description=e.description
        ), e.code

    @app.before_request
    def before_request():
        g.redis_client = get_redis_client()

    @app.route('/healthz', methods=['GET'])
    def health():
        return "OK"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)