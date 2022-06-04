from flask import Blueprint

from utils.auth import BasicAuthentication
from utils.middleware import AuthenticationMiddleware


bp = Blueprint('api', __name__, url_prefix='/api')


@bp.before_request
def auth_middleware():
    AuthenticationMiddleware(
        authentication_classes=[BasicAuthentication]
    )()
