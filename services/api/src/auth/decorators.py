from datetime import datetime
from functools import wraps
import os
import pickle

from flask import abort, g, request

from db import redis_client
from auth.models import AccessToken, RefreshToken, Client, User, Throttle


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


def throttle(identifier_type, max_requests, sliding_window):
    identifier_type = identifier_type.upper()
    if identifier_type not in ('USER', 'ANON'):
        raise ValueError("Invalid identifier type")

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if identifier_type == 'USER':
                identifier = g.access_token.user_id

            elif identifier_type == 'ANON':
                identifier = request.headers.get('X-Forwarded-For')
                if not identifier:
                    identifier = request.remote_addr

            # !! use the appropriate throttle class  !!
            key = '{}:{}'.format(request.path, identifier)
            throttle = Throttle.from_cache(key)
            if throttle is None:
                throttle = Throttle()

            throttle.slide_window()
            throttle.increment()
            if throttle.exceeded_max_requests():
                abort(429)

            throttle.to_redis()

            return func(*args, **kwargs)
        return wrapper
    return decorator


max_requests = int(os.getenv('RATE_LIMIT_MAX_REQUESTS'))
sliding_window = int(os.getenv('RATE_LIMIT_SLIDING_WINDOW'))

user_throttle = throttle('USER', max_requests, sliding_window)
anon_throttle = throttle('ANON', max_requests, sliding_window)
