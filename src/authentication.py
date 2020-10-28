import os
from base64 import b64decode
from functools import wraps
from hashlib import sha256
import hmac
import time
from flask import current_app, g, request
import jwt
from werkzeug.exceptions import BadRequest, Unauthorized
from cache import Cache
from models.users import User


class BaseAuthenticator:
    scheme = None 
    realm = None

    @property
    def www_authenticate(self):
        if self.realm:
            return '{} realm={}'.format(self.scheme, self.realm)
        return self.scheme

    def authenticate(self):
        authorization = request.headers.get('Authorization')
        if not authorization:
            raise BadRequest('Missing Authorization header.')

        scheme, _, credentials = authorization.partition(' ')
        if not scheme:
            raise BadRequest('Invalid Authorization header.')

        if scheme != self.scheme:
            raise Unauthorized(www_authenticate=self.www_authenticate)

        return self.validate_credentials(credentials)

    def validate_credentials(self, credentials):
        pass


class BasicAuthenticator(BaseAuthenticator):
    scheme = 'Basic'
    
    def validate_credentials(self, credentials):
        decoded_credentials = b64decode(credentials)
        username, _, password = decoded_credentials.partition(':')

        user = User.objects.filter(username=username).first()
        if not user:
            raise Unauthorized(
                'Invalid username or password.',
                www_authenticate=self.www_authenticate
            )

        if not user.check_password(password):
            raise Unauthorized(
                'Invalid username or password.',
                www_authenticate=self.www_authenticate
            )

        return (user, None)


class JWTAuthenticator(BaseAuthenticator):
    scheme = 'Bearer'

    def validate_credentials(self, credentials):
        jwt_secret_key = os.getenv('JWT_SECRET_KEY')
        try:
            headers = jwt.get_unverified_header(credentials)
            payload = jwt.decode(credentials, jwt_secret_key)

        except Exception as e:
            current_app.logger.warning(e)
            raise Unauthorized(
                'Invalid token.', 
                www_authenticate=self.www_authenticate
            )

        if headers.get('typ') != 'at+jwt':
            raise Unauthorized(
                'Invalid Token.',
                www_authenticate=self.www_authenticate
            )

        sub = payload.get('sub')
        return (sub, credentials)


class HMACAuthenticator(BaseAuthenticator):    
    """
        Example:
        Authorization: HMAC-SHA256 username:signature
    """
    scheme = 'HMAC-SHA256'

    def __init__(self):
        self.timestamp_header = os.getenv('HMAC_TIMESTAMP_HEADER', 'Timestamp')
        self.nonce_header = os.getenv('HMAC_NONCE_HEADER', 'Nonce')
        self.timestamp_threshold = os.getenv('HMAC_TIMESTAMP_THRESHOLD', 300)

    def validate_credentials(self, credentials):
        username, _, signature = credentials.partition(':')
        timestamp = float(request.headers.get(self.timestamp_header, 0))
        nonce = request.headers.get(self.nonce_header)

        key = self.get_key(username)
        payload = request.query_string if request.method == 'GET' else request.data
        payload = payload.decode()
        message = '{}{}{}{}{}'.format(
            request.method,
            request.base_url,
            payload,
            timestamp, 
            nonce
        )

        h = hmac.HMAC(key=key.encode(), msg=message.encode(), digestmod=sha256)
        calculated_signature = h.hexdigest()

        if signature != calculated_signature:
            raise Unauthorized(
                'Invalid siganture.',
                www_authenticate=self.www_authenticate
            )

        self.check_timestamp(timestamp)
        self.check_nonce(username, nonce)

    def check_timestamp(self, timestamp):       
        diff = time.time() - timestamp
        if diff > self.timestamp_threshold:
            raise Unauthorized(
                'Expired timestamp.',
                www_authenticate=self.www_authenticate
            )

    def check_nonce(self, username, nonce):
        cache = Cache(key_prefix='nonce', timeout=self.timestamp_threshold)
        key = '{}:{}'.format(username, nonce)
        if key in cache:
            raise Unauthorized(
                'Nonce used more than once.',
                www_authenticate=self.www_authenticate
            )
        cache.set(key, '')

    def get_key(self, username):
        """
            return the key associated with the username
        """
        return ''


def decorator_factory(authenticator_class):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            authenticator = authenticator_class()
            authenticator.authenticate()
            return func(*args, **kwargs)
        return wrapper
    return decorator


basic_auth = decorator_factory(BasicAuthenticator)
jwt_auth = decorator_factory(JWTAuthenticator)
hmac_auth = decorator_factory(HMACAuthenticator)