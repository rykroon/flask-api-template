from flask import g, Flask
from core.json_util import JSONEncoder
from db import get_redis_client


def create_app():
    app = Flask(__name__)
    app.json_encoder = JSONEncoder

    from core.error_handlers import error_handlers
    for code, handler in error_handlers.items():
        app.register_error_handler(code, handler)

    from auth import blueprint as auth_bp
    app.register_blueprint(auth_bp)

    # from app import blueprint as app_bp
    # app.register_blueprint(app_bp)

    @app.before_request
    def before_request():
        g.redis_client = get_redis_client()

    @app.route('/health', methods=['GET'])
    def health():
        return "Alive!"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)