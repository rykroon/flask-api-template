from flask import Blueprint, g, jsonify, request
from flask.views import MethodView

from restapi.throttling import throttle
from models import Client


bp = Blueprint('tokens', __name__)


class Token(MethodView):
    decorators = [throttle(rate='1/s', scope='tokens')]

    def post(self):
        client_id = request.json.get('client_id')
        client = Client.objects.get(id=client_id)

        grant_type = request.json.get('grant_type')

        if grant_type == 'password':
            return self.password_grant()

        if grant_type == 'refresh_token':
            return self.refresh_token_grant()

    def password_grant(self):
        username = request.json.get('username')
        password = request.json.get('password')

        # user = User.objects.get(email_address=username)
        # if not user.check_password(password):
        #     raise Exception

        return jsonify(
            access_token='',
            token_type='bearer',
            expires_in='',
            refresh_token=''
        )

    def refresh_token_grant(self):
        pass
        

