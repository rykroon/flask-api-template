from .authorize import bp as authorize_bp
from .tokens import bp as token_bp
from .users import bp as user_bp

blueprints = [authorize_bp, token_bp, user_bp]