from flask import Blueprint, g, jsonify, request
from flask.views import MethodView

from authentication import basic_auth
from throttling import throttle


bp = Blueprint('tokens', __name__)


class Token(MethodView):
    decorators = [basic_auth, throttle(rate='1/s', scope='tokens')]

    def post(self):
        pass
        

