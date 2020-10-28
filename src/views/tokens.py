from flask import Blueprint, g, jsonify, request
from flask.views import MethodView

from authentication import basic_auth
from throttling import throttle


bp = Blueprint('tokens', __name__)


class Token(MethodView):
    decorators = [basic_auth, throttle(scope='tokens', rate='1/s')]

    def post(self):
        pass
        

