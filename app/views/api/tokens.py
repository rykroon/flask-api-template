import time

from flask import Blueprint, g, request
from flask.json import jsonify
import jwt

from utils.views import APIView


bp = Blueprint('tokens', __name__)


class TokenView(APIView):

    def post(self):
        token = jwt.encode({
            'sub': str(g.client.pk),
            'iss': request.host,
            'exp': time.time() + (60 * 60)
        }, g.client.secret_key)
        return jsonify({'token': token})


token_view = TokenView.as_view('TokenView')
bp.add_url_rule('/tokens', view_func=token_view, methods=['POST'])
