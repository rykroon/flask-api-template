import os 
from flask import abort, g, request
from auth.models import AccessToken, RefreshToken, Client, User


def auth(func):
    """
        A Decorator for authenticating a user with an Access Token
    """
    def decorator(*args, **kwargs):
        if os.getenv('FLASK_ENV') == 'development':
            if os.getenv('NO_AUTH') == 'true':
                client = Client.query.filter(no_auth=True).one_or_none()
                user = User.query.filter(no_auth=True).one_or_none()
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

        access_token = AccessToken.get(token)
        if access_token is None:
            abort(401, "Invalid Access Token")

        g.access_token = access_token
        return func(*args, **kwargs)

    return decorator

