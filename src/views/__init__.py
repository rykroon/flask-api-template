from flask import Blueprint
from views.api import bp as api_bp


bp = Blueprint('views', __name__)
bp.register_blueprint(api_bp)
    