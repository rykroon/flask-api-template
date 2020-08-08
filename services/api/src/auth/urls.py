from flask import Blueprint
from auth.views import AuthorizationView, TokenView, UserInfoView, UserView

blueprint = Blueprint('auth', __name__)

#authorization view
authorization_view = AuthorizationView.as_view('authorization_view')
blueprint.add_url_rule('/oauth/authorize', view_func=authorization_view, methods=['GET', 'POST'])

#token view
token_view = TokenView.as_view('token_view')
blueprint.add_url_rule('/oauth/token', view_func=token_view, methods=['POST'])

#user info view
userinfo_view = UserInfoView.as_view('userinfo_view')
blueprint.add_url_rule('/oauth/userinfo', view_func=userinfo_view, methods=['GET', 'POST'])

#user view
user_view = UserView.as_view('user_view')
user_view_with_auth = UserView.as_view('user_view_with_auth')

blueprint.add_url_rule('/users', view_func=user_view_with_auth, methods=['GET'])
blueprint.add_url_rule('/users', view_func=user_view, methods=['POST'])
blueprint.add_url_rule('/users/<string:id>', view_func=user_view_with_auth, methods=['GET', 'PUT', 'DELETE'])


