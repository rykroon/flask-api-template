from base64 import b64decode
from functools import wraps
from flask import abort, g, request
from auth.models import User, AccessToken


class BaseAuthentication:
    """
    All authentication classes should extend BaseAuthentication.
    """

    def authenticate(self):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        raise NotImplementedError(".authenticate() must be overridden.")

    def authenticate_header(self):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        pass


class SchemeAuthentication(BaseAuthentication):
    """
        Authentication using the Authorization Header
    """
    scheme = None
    realm = 'api'

    def authenticate(self):
        authorization = request.headers.get('Authorization')
        if authorization is None:
            abort(400, "Missing Authorization header")
        
        try:
            scheme, credentials = authorization.split()
        except ValueError:
            abort(400, "Invalid Authorization header")
        
        if scheme != self.scheme:
            abort(400, "Invalid authentication scheme")

        return self.authenticate_credentials(credentials)
    
    def authenticate_credentials(self, credentials):
        raise NotImplementedError

    def authenticate_header(self, request):
        return '{} realm="{}"'.format(self.scheme, self.realm)


class BasicAuthentication(SchemeAuthentication):
    scheme = 'Basic'

    def authenticate_credentials(self, credentials):
        decoded_credentials = b64decode(credentials).decode()
        try:
            username, password = decoded_credentials.split(':')
        except ValueError:
            abort(400)

        user = User.objects.filter(email=username).first()
        if user is None:
            abort(401, "invalid username or password")

        if not user.verify_password(password):
            abort(401, "invalid username or password")

        return user, None


class BearerAuthentication(SchemeAuthentication):
    scheme = 'Bearer'


class TokenAuthentication(BearerAuthentication):
    token_class = None

    def authenticate_credentials(self, credentials):
        token = self.token_class.from_cache(credentials)
        if token is None:
            return None

        return token.get_user(), token


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
