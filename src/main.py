from flask import Flask

from utils.error_handlers import error_handlers
from utils.logging import get_logger
from views import bp as views_bp


def create_app():
    app = Flask(__name__)

    #logger
    app.logger = get_logger()

    #blueprints
    app.register_blueprint(views_bp)

    #exception handlers
    for exc, handler in error_handlers.items():
        app.register_error_handler(exc, handler)

    @app.route('/healthz', methods=['GET'])
    def health():
        return "OK"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
