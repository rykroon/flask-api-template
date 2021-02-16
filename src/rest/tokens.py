import os
import time
import uuid
import jwt

jwt_secret_key = os.getenv('JWT_SECRET_KEY')
jwt_access_token_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)) #defaults to 15 minutes
jwt_refresh_token_expires = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 3600))


def validate_access_token(at):
    headers = jwt.get_unverified_header(at)
    if headers.get('typ') != 'at+jwt':
        raise Exception('Invalid Access Token.')
    return validate_token(at)


def validate_refresh_token(rt):
    headers = jwt.get_unverified_header(rt)
    if headers.get('typ') != 'rt+jwt':
        raise Exception('Invalid Refresh Token.')
    return validate_token(rt)


def validate_token(token):
    try:
        return jwt.decode(
            token,
            key=jwt_secret_key
        )
    except Exception as e:
        raise e


def create_access_token(sub):
    return create_token(
        typ='at+jwt',
        sub=sub,
        exp=jwt_access_token_expires
    )


def create_refresh_token(sub):
    return create_token(
        typ='rt+jwt',
        sub=sub,
        exp=jwt_refresh_token_expires
    )


def create_token(typ, sub, exp):
    headers = dict(
        typ=typ
    )
    now = time.time()
    payload = dict(
        sub=sub,
        exp=now + exp,
        iat=now,
        jti=str(uuid.uuid4())
    )

    return jwt.encode(payload, key=jwt_secret_key, headers=headers)