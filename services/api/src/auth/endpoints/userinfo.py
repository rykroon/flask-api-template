from flask import Blueprint, g, jsonify
from auth.views import OAuthView
from auth.models import User
from auth.decorators import auth

bp = Blueprint('userinfo', __name__)


class UserInfo(OAuthView):

    def get(self):
        return self._userinfo()

    def post(self):
        return self._userinfo()

    def _userinfo(self):
        user = g.access_token.user
        return jsonify(user.info())


userinfo_view = auth(UserInfo.as_view('userinfo_view'))
bp.add_url_rule('/oauth/authorize', view_func=userinfo_view, methods=['GET', 'POST'])