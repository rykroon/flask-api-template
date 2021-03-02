from flask import Blueprint, g, jsonify, request
from flask.views import MethodView
import jwt
import os
import time
import uuid

from rest import APIView
from models import Client


bp = Blueprint('tokens', __name__)


jwt_access_token_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 60 * 15))


class TokenView(APIView):

    def post(self):
        headers = {
            'typ': 'at+jwt', 
            'kid': g.client.pk
        }

        now = time.time()

        payload = {
            'iss': request.base_url,
            'sub': g.client.pk,
            'exp': now + jwt_access_token_expires,
            'iat': now,
            'jti': str(uuid.uuid4())
        }

        token = jwt.encode(
            payload=payload, 
            key=g.client.secret_key, 
            headers=headers
        )

        return jsonify(
            access_token=token,
            token_type='bearer',
            expires_in=jwt_access_token_expires,
        )

