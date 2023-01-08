from base64 import b64decode

from flask import request
from werkzeug.exceptions import Unauthorized


class AuthenticationBackend:

    def authenticate(self):
        raise NotImplementedError


class SchemeAuthentication(AuthenticationBackend):

    scheme = None

    def authenticate(self):
        authorization = request.headers.get('Authorization')
        if authorization is None:
            return

        scheme, _, credentials = authorization.partition(' ')
        if scheme.lower() != self.scheme:
            return

        return self.validate_credentials(credentials)

    def validate_credentials(self, credentials):
        raise NotImplementedError


class BasicAuthentication(SchemeAuthentication):
    scheme = 'basic'

    def validate_credentials(self, credentials):
        decoded_credentials = b64decode(credentials).decode()
        username, _, password = decoded_credentials.partition(':')
        return self.validate_user(username, password)

    def validate_user(self, username, password):
        raise NotImplementedError


class BearerAuthentication(SchemeAuthentication):
    scheme = 'bearer'

