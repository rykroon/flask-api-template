from datetime import datetime
from functools import wraps
import os
import pickle

from flask import abort, g, request

from db import redis_client
from auth.models import AccessToken, RefreshToken, Client, User


def auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if os.getenv('FLASK_ENV') == 'development':
            if os.getenv('NO_AUTH') == 'true':
                client = Client.objects.filter(no_auth=True).first()
                user = User.objects.filter(no_auth=True).first()
                g.access_token = AccessToken(client, user)
                return func(*args, **kwargs)
       
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
            abort(401, "Invalid Access Token")

        g.user = access_token.get_user()

        return func(*args, **kwargs)
    return wrapper
