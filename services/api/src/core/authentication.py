from base64 import b64decode
from flask import abort, current_app, g, request
from auth.models import User, AccessToken
from core import exceptions


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
        auth = request.headers.get('Authorization', '').split()
        if not auth or auth[0].lower() != self.scheme:
            return None

        if len(auth) == 1:
            msg = 'Invalid {} header. No credentials provided.'.format(self.scheme)
            raise exceptions.AuthenticationFailed(msg)

        elif len(auth) > 2:
            msg = 'Invalid {} header. Credentials string should not contain spaces.'.format(self.scheme)
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1])
    
    def authenticate_credentials(self, credentials):
        raise NotImplementedError

    def authenticate_header(self, request):
        return '{} realm="{}"'.format(self.scheme, self.realm)


class BasicAuthentication(SchemeAuthentication):
    scheme = 'basic'

    def authenticate_credentials(self, credentials):
        try:
            decoded_credentials = b64decode(credentials).decode()
            credential_parts = decoded_credentials.partition(':')
        except:
            msg = 'Invalid basic header. Credentials not correctly base64 encoded.'
            raise exceptions.AuthenticationFailed(msg)

        username, password = credential_parts[0], credential_parts[2]

        user = User.objects.filter(email=username).first()
        if user is None or not user.verify_password(password):
            raise exceptions.AuthenticationFailed('Invalid username/password.')

        if not user.is_active():
            raise exceptions.AuthenticationFailed('User inactive or deleted.')

        return (user, None)


class BearerAuthentication(SchemeAuthentication):
    scheme = 'bearer'


class TokenAuthentication(BearerAuthentication):
    token_class = None

    def authenticate_credentials(self, credentials):
        token = self.token_class.from_cache(credentials)
        if token is None:
            return None

        return (token.get_user(), token)

