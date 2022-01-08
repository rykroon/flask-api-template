from flask import Blueprint

from utils.auth import BasicAuthentication
from utils.middleware import AuthenticationMiddleware
from views.api import bp as api_bp


bp = Blueprint('views', __name__)

bp.register_blueprint(api_bp)
    