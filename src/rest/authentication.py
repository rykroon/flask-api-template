import os
from base64 import b64decode
from functools import wraps
from hashlib import sha256
import hmac
import time

from flask import current_app, g, request
import jwt
from werkzeug.exceptions import BadRequest, Unauthorized

from utils import Cache
from models import Client


class BaseAuthentication:
    scheme = None 
    realm = None

    @property
    def www_authenticate(self):
        if self.realm:
            return '{} realm={}'.format(self.scheme, self.realm)
        return self.scheme

    def authenticate(self):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            return None

        scheme, _, credentials = authorization_header.partition(' ')
        if not credentials:
            raise BadRequest('Invalid Authorization header.')

        if scheme.upper() != self.scheme:
            return None

        return self.validate_credentials(credentials)

    def validate_credentials(self, credentials):
        raise NotImplementedError


class BasicAuthentication(BaseAuthentication):
    scheme = 'BASIC'
    
    def validate_credentials(self, credentials):
        decoded_credentials = b64decode(credentials)
        client_id, _, secret_key = decoded_credentials.partition(':')

        client = Client.objects.filter(pk=client_id).first()
        if not client:
            raise Unauthorized(
                'Invalid username or password.',
                www_authenticate=self.www_authenticate
            )

        if client.secret_key != secret_key:
            raise Unauthorized(
                'Invalid username or password.',
                www_authenticate=self.www_authenticate
            )

        return client


class TokenAuthentication(BaseAuthentication):
    scheme = 'BEARER'

    def validate_credentials(self, credentials):
        headers = jwt.get_unverified_header(credentials)
        if headers.get('typ') != 'at+jwt':
            raise Unauthorized

        client_id = headers.get('kid')
        client = Client.objects.filter(pk=client_id).first()
        if client is None:
            raise Unauthorized

        try:
            payload = jwt.decode(
                credentials, 
                key=client.secret_key, 
                issuer=request.base_url
            )
        except Exception as e:
            raise Unauthorized

        return client


class HMACAuthentication(BaseAuthentication):    
    """
        Example:
        Authorization: HS256 username:signature
    """
    scheme = 'HS256'

    def __init__(self):
        self.timestamp_header = os.getenv('HMAC_TIMESTAMP_HEADER', 'Timestamp')
        self.nonce_header = os.getenv('HMAC_NONCE_HEADER', 'Nonce')
        self.timestamp_threshold = os.getenv('HMAC_TIMESTAMP_THRESHOLD', 300)

    def validate_credentials(self, credentials):
        decoded_credentials = b64decode(credentials)
        client_id, _, signature = decoded_credentials.partition(':')
        timestamp = request.headers.get(self.timestamp_header, 0)
        nonce = request.headers.get(self.nonce_header)

        client = Client.objects.filter(pk=client_id).first()
        if not client:
            raise Unauthorized(
                'Invalid client id.',
                www_authenticate=self.www_authenticate
            )

        path = request.full_path if request.query_string else request.path

        message = '{}{}{}{}{}'.format(
            request.method,
            path,
            request.get_data().decode(),
            timestamp, 
            nonce
        )

        h = hmac.HMAC(key=client.secret_key.encode(), msg=message.encode(), digestmod=sha256)
        calculated_signature = h.hexdigest()

        if signature != calculated_signature:
            raise Unauthorized(
                'Invalid siganture.',
                www_authenticate=self.www_authenticate
            )

        self.check_timestamp(float(timestamp))
        self.check_nonce(client, nonce)

        return client

    def check_timestamp(self, timestamp):       
        diff = time.time() - timestamp
        if diff > self.timestamp_threshold:
            raise Unauthorized(
                'Expired timestamp.',
                www_authenticate=self.www_authenticate
            )

    def check_nonce(self, client, nonce):
        cache = Cache(key_prefix='nonce', timeout=self.timestamp_threshold)
        key = '{}:{}'.format(client.pk, nonce)
        if key in cache:
            raise Unauthorized(
                'Nonce used more than once.',
                www_authenticate=self.www_authenticate
            )
        cache.set(key, '')
