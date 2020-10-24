import os
from datetime import datetime as dt, timedelta as td
from functools import wraps
import uuid

from flask import g, request
import jwt
from werkzeug.exceptions import BadRequest, Unauthorized

from authentication import JWTAuthentication

jwt_secret_key = os.getenv('JWT_SECRET_KEY')
jwt_access_token_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)) #defaults to 15 minutes


def jwt_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        authenticator = JWTAuthentication()
        g.user, g.token = authenticator.authenticate()
        return func(*args, **kwargs)

    return wrapper


def create_access_token(sub):
    payload = dict(
        sub=sub,
        exp=dt.utcnow() + td(seconds=jwt_access_token_expires),
        iat=dt.utcnow(),
        jti=str(uuid.uuid4())
    )

    return jwt.encode(payload, key=jwt_secret_key)