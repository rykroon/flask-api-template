from base64 import b64decode
from flask import g, request
import jwt
from werkzeug.exceptions import BadRequest, Unauthorized


class BaseAuthentication:
    scheme = None
    realm = None

    def authenticate(self):
        auth = request.headers.get('Authorization')
        if not auth:
            raise BadRequest('Missing Authorization header.')

        scheme, _, credentials = auth.partition(' ')
        if scheme != self.scheme:
            e = Unauthorized("Invalid Authorization scheme.")
            e.headers = self.authenticate_header()
            raise e

        return self.validate_credentials(credentials)

    def validate_credentials(self, credentials):
        pass

    def authenticate_header(self):
        return {
            'WWW-Authenticate': '{type} realm={realm}'.format(
                type=self.scheme, 
                realm=self.realm
            )
        }


class BasicAuthentication(BaseAuthentication):
    scheme = 'Basic'

    def validate_credentials(self, credentials):
        decoded_creds = b64decode(credentials)
        username, _, password = decoded_creds.partition(':')

        return self.validate_user(username, password)

    def validate_user(self, username, password):
        pass


class JWTAuthentication(BaseAuthentication):
    scheme = 'Bearer'

    def validate_credentials(self, credentials):
        try:
            payload = jwt.decode(credentials)
        except Exception as e:
            raise Unauthorized(str(e))

        return (payload.get('sub'), credentials)

