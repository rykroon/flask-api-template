from flask import Flask
from core.json_util import JSONEncoder


def create_app():
    app = Flask(__name__)
    app.json_encoder = JSONEncoder

    from core.error_handlers import error_handlers
    for code, handler in error_handlers.items():
        app.register_error_handler(code, handler)

    from auth.endpoints import blueprints as auth_blueprints
    for bp in auth_blueprints:
        app.register_blueprint(bp)

    from app.endpoints import blueprints as app_blueprints
    for bp in app_blueprints:
        app.register_blueprint(bp)

    @app.route('/health', methods=['GET'])
    def health():
        return "Alive!"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)