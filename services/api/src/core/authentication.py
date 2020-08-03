from functools import wraps
from flask import abort, g, request
from auth.models import User, AccessToken


class BaseAuthentication:
    def authenticate(self):
        raise NotImplementedError


class BasicAuthentication(BaseAuthentication):
    def authenticate(self):
        if not request.authorization:
            pass

        username = request.authorization.get('username')
        password = request.authorization.get('password')

        user = User.objects.get(email=username)
        if not user.verify_password(password):
            return None

        return user


class TokenAuthentication(BaseAuthentication):
    def authenticate(self):
        authorization = request.headers.get('Authorization')
        if authorization is None:
            abort(400, "Missing Authorization header")
        
        try:
            scheme, token = authorization.split(' ')
        except:
            abort(400, "Invalid Authorization header")
        
        if scheme != 'Bearer':
            abort(400, "Invalid authentication scheme")

        access_token = AccessToken.from_cache(token)
        if access_token is None:
            return None

        return access_token.get_user()


def auth(auth_class):
    def decorator(func):
        @wraps
        def wrapper(*args, **kwargs):
            auth = auth_class()
            user = auth.authenticate()
            if user is None:
                abort(401)
            g.user = user
            return func(*args, **kwargs)
        return wrapper
    return decorator


basic_auth = auth(BasicAuthentication)
token_auth = auth(TokenAuthentication)
