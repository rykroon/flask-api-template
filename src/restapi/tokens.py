import os
from datetime import datetime as dt, timedelta as td
import uuid
import jwt

jwt_secret_key = os.getenv('JWT_SECRET_KEY')
jwt_access_token_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)) #defaults to 15 minutes
jwt_refresh_token_expires = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 3600))

def create_access_token(sub):
    headers = dict(
        typ='at+jwt'
    )
    payload = dict(
        sub=sub,
        exp=dt.utcnow() + td(seconds=jwt_access_token_expires),
        iat=dt.utcnow(),
        jti=str(uuid.uuid4())
    )

    return jwt.encode(payload, key=jwt_secret_key, headers=headers)


def create_refresh_token(sub):
    headers = dict(
        typ='rt+jwt'
    )
    payload = dict(
        sub=sub,
        exp=dt.utcnow() + td(seconds=jwt_refresh_token_expires),
        iat=dt.utcnow(),
        jti=str(uuid.uuid4())
    )

    return jwt.encode(payload, key=jwt_secret_key, headers=headers)