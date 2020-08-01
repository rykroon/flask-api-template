from flask import Blueprint
from auth.views import AuthorizationView, TokenView, UserInfoView, UserView
from auth.decorators import auth, anon_throttle, user_throttle

blueprint = Blueprint('auth', __name__)

#authorization view
authorization_view = anon_throttle(AuthorizationView.as_view('authorization_view'))
blueprint.add_url_rule('/oauth/authorize', view_func=authorization_view, methods=['GET', 'POST'])

#token view
token_view = anon_throttle(TokenView.as_view('token_view'))
blueprint.add_url_rule('/oauth/token', view_func=token_view, methods=['POST'])

#user info view
userinfo_view = auth(user_throttle(UserInfoView.as_view('userinfo_view')))
blueprint.add_url_rule('/oauth/userinfo', view_func=userinfo_view, methods=['GET', 'POST'])

#user view
user_view = anon_throttle(UserView.as_view('user_view'))
user_view_with_auth = auth(user_throttle(UserView.as_view('user_view_with_auth')))

blueprint.add_url_rule('/users', view_func=user_view_with_auth, methods=['GET'])
blueprint.add_url_rule('/users', view_func=user_view, methods=['POST'])
blueprint.add_url_rule('/users/<string:id>', view_func=user_view_with_auth, methods=['GET', 'PUT', 'DELETE'])


