from functools import wraps
from flask import abort, g, request
from auth.models import User, AccessToken


class BaseAuthentication:
    def authenticate(self):
        raise NotImplementedError

    def authenticate_header(self):
        raise NotImplementedError


class SchemeAuthentication(BaseAuthentication):
    """
        Authentication using the Authorization Header
    """
    scheme = None

    def authenticate(self):
        authorization = request.headers.get('Authorization')
        if authorization is None:
            abort(400, "Missing Authorization header")
        
        try:
            scheme, credentials = authorization.split(' ')
        except ValueError:
            abort(400, "Invalid Authorization header")
        
        if scheme != self.scheme:
            abort(400, "Invalid authentication scheme")

        return self.validate_credentials(credentials)
    
    def validate_credentials(self, credentials):
        raise NotImplementedError


class BasicAuthentication(SchemeAuthentication):
    scheme = 'Basic'

    def authenticate(self):
        if not request.authorization:
            abort(400, 'Invalid Authroization header')

        username = request.authorization.get('username')
        password = request.authorization.get('password')

        return self.validate_credentials(username, password)

    def validate_credentials(self, username, password):
        user = User.objects.get(email=username)
        if not user.verify_password(password):
            return None
        return user


class BearerAuthentication(SchemeAuthentication):
    scheme = 'Bearer'


class TokenAuthentication(BearerAuthentication):
    token_class = None

    def validate_credentials(self, token):
        token_object = self.token_class.from_cache(token)
        if token_object is None:
            return None

        return token_object.get_user()


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
