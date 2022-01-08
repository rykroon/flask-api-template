from flask import Blueprint

from utils.auth import BasicAuthentication
from utils.middleware import AuthenticationMiddleware
from views.api.tokens import bp as tokens_bp


bp = Blueprint('api', __name__, url_prefix='/api')


@bp.before_request
def auth_middleware():
    AuthenticationMiddleware(
        authentication_classes=[BasicAuthentication]
    )()


bp.register_blueprint(tokens_bp)