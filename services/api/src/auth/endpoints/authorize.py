from datetime import datetime, timedelta
from flask import Blueprint, abort, current_app, jsonify, request
from auth.models import AuthorizationCode, Client, User
from auth.views import OAuthView

bp = Blueprint('authorize', __name__)


class AuthorizationAPI(OAuthView):

    def get(self):
        return self._authorize()

    def post(self):
        return self._authorize()

    def _authorize(self):
        username = self._get_username()
        password = self._get_password()

        client = self._get_client()
        if client.is_confidential():
            abort(401, "Client not authorized to use the Authorization Code Flow")

        code_challenge = self._get_param('code_challenge')
        code_challenge_method = self._get_param('code_challenge_method')
        if code_challenge_method not in AuthorizationCode.CODE_CHALLENGE_METHODS:
            abort(400, "Invalid code_challenge_method")
        
        # validate credentials
        user = User.query.filter(email=username).one_or_none()
        if user is None:
            abort(401, "Invalid username or password")

        self._login(user, password)
        scope = request.form.get('scope')

        auth_code = AuthorizationCode(client, user, scope)
        auth_code.code_challenge = code_challenge
        auth_code.code_challenge_method = code_challenge_method

        auth_code.save()

        return jsonify(
            code=str(auth_code)
        )

    def _login(self, user, password):
        MAX_LOGIN_ATTEMPTS = 10
        LOCKOUT_PERIOD = timedelta(minutes=30)

        if user.lockout_date:
            if user.lockout_date + LOCKOUT_PERIOD > datetime.utcnow():
                abort(401, "Account is locked due to too many failed login attempts")

            user.lockout_date = None
            user.failed_login_attempts = 0
            user.save()

        if not user.check_password(password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts > MAX_LOGIN_ATTEMPTS:
                user.lockout_date = datetime.utcnow()

            user.save()
            abort(401, "Invalid username or password")

        user.failed_login_attempts = 0
        user.save()

        return True


authorize_view = AuthorizationAPI.as_view('authorize_view')
bp.add_url_rule('/oauth/authorize', view_func=authorize_view, methods=['GET', 'POST'])