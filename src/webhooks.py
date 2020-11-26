from hashlib import sha256
import hmac
import time
import uuid
import requests
from requests.auth import AuthBase


class Webhook:
    def __init__(self, url, event_type, data, method='POST', auth=None):
        self.method = method
        self.url = url
        self.event_type = event_type
        self.data = data
        self.auth = auth

    def send(self):
        payload = dict(
            event_type=self.event_type,
            data=self.data
        )
        return requests.request(method=self.method, url=self.url, auth=self.auth, json=payload)


class WebhookHMACAuth(AuthBase):
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def __call__(self, req):
        timestamp = str(time.time())
        nonce = str(uuid.uuid4().int)
        message = '{}{}{}'.format(req.body, timestamp, nonce)

        h = hmac.HMAC(self.secret_key.encode(), message.encode(), sha256)
        signature = h.hexdigest()

        req.headers.update({
            'Signature': signature,
            'Timestamp': timestamp,
            'Nonce': nonce
        })

        return req

        

