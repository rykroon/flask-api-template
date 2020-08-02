from datetime import datetime, timedelta
from flask import abort, current_app, g, jsonify, request
from flask.views import MethodView

from auth.decorators import auth, user_throttle, anon_throttle
from auth.models import AccessToken, AuthorizationCode, Client, RefreshToken, User
from core.views import DocumentView


class ResourceView(DocumentView):
    """
        A DocumentView more focused on a 'Resource'
        has additional auth related functionality
    """

    read_scope = None
    write_scope = None

    def _authorize(self, resource):
        if self._no_auth:
            return

        is_authorized = g.access_token.user_id == resource.user_id
        if is_authorized:
            if request.method == 'GET':
                is_authorized = g.access_token.scope == self.__class__.read_scope
            else:
                is_authorized = g.access_token.scope == self.__class__.write_scope
                
        if not is_authorized:
            abort(403, 'Not authorized to the resource')

    def _retrieve_document(self, id):
        document = super()._retrieve_document(id)
        if not g.user.pk == document.user_id:
            abort(403, "Not authorized to the resource")
        return document
    
    def _get_queryset(self):
        qs = super()._get_queryset()
        qs = qs.filter(user=g.user.pk)
        return qs

    def _create_document(self):
        document = super()._create_document()
        document.user_id = g.user.pk
        return document

    @classmethod
    def as_view(cls, name, use_auth=True, *args, **kwargs):
        view = super().as_view(name, *args, **kwargs)
        if use_auth:
            return auth(user_throttle(view))
        else:
            return anon_throttle(view)


class OAuthView(MethodView):

    def _get_client(self, basic_auth=False):
        if basic_auth:
            client_id = self._get_username()
        else:
            client_id = self._get_param('client_id')

        client = Client.objects.get(client_id)
        if not client:
            abort(401, "Invalid client_id")

        return client

    def _get_param(self, parameter, required=True):
        if request.method == 'GET':
            value = request.args.get(parameter)
            
        if request.method == 'POST':
            value = request.form.get(parameter)

        if required and not value:
            abort(400, "Missing parameter '{}'".format(parameter))
        return value

    def _get_username(self):
        if not request.authorization:
            abort(400, "Invalid Authorization header")

        username = request.authorization.get('username')
        if not username:
            abort(400, "Missing username")

        return username

    def _get_password(self, required=True):
        if not request.authorization:
            abort(400, "Invalid Authorization header")
        
        password = request.authorization.get('password')
        if not password:
            abort(400, "missing password")

        return password


class AuthorizationView(OAuthView):

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
        user = User.objects.filter(email=username).first()
        if user is None:
            abort(401, "Invalid username or password")

        self._login(user, password)
        scope = self._get_param('scope', required=False)

        auth_code = AuthorizationCode(client, user, scope)
        auth_code.code_challenge = code_challenge
        auth_code.code_challenge_method = code_challenge_method

        auth_code.to_redis()

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


class TokenView(OAuthView):

    def post(self):
        grant_type = self._get_param('grant_type')
        if grant_type == 'authorization_code':
            return self._authorization_code_grant()

        elif grant_type == 'refresh_token':
            return self._refresh_token_grant()

        else:
            abort(400, "Invalid grant_type")

    def _authorization_code_grant(self):
        code = self._get_param('code')
        auth_code = AuthorizationCode.from_redis(code)
        if auth_code is None:
            abort(401, "Invalid authorization_code")

        client = self._get_client()

        if auth_code.client_id != client.pk:
            abort(401, "client_id does not match with the client_id of the authorization code")

        if auth_code.code_challenge:
            code_verifier = self._get_param('code_verifier')
            if 43 < len(code_verifier) < 128:
                abort(400, "Invalid code_verifier length")

            if not auth_code.verify_code_challenge(code_verifier):
                abort(401, "code_verifier does not match code_challenge")

        refresh_token = RefreshToken(
            client=auth_code.client,
            user=auth_code.user,
            scope=auth_code.scope
        )

        access_token = AccessToken(
            client=auth_code.client,
            user=auth_code.user,
            scope=auth_code.scope
        )

        refresh_token.to_redis()
        access_token.to_redis()
        auth_code.delete()

        return jsonify(
            access_token=str(access_token),
            token_type='Bearer',
            expires_in=AccessToken.ttl,
            refresh_token=str(refresh_token)
        )

    def _client_credentials(self):
        client = self._get_client(basic_auth=True)
        if not client.is_confidential():
            abort(401, "Client is unauthorized to use the 'client_credentials' grant type")

        client_secret = self._get_password()
        if client.secret != client_secret:
            abort(401, "Invalid client_secret")

        #don't return refresh token
        access_token = AccessToken(client)
        return jsonify(
            access_token=str(access_token),
            token_type='Bearer',
            expires_in=AccessToken.ttl
        )

    def _refresh_token_grant(self):   
        refresh_token = self._get_param('refresh_token')
        refresh_token = RefreshToken.from_redis(refresh_token)
        if refresh_token is None:
            abort(401, "Invalid refresh_token")

        client = self._get_client()

        if refresh_token.client_id != client.pk:
            abort(401, "Incorrect refresh_token for the given client_id")

        new_refresh_token = RefreshToken(
            client=refresh_token.client,
            user=refresh_token.user,
            scope=refresh_token.scope
        )

        access_token = AccessToken(
            client=refresh_token.client,
            user=refresh_token.user,
            scope=refresh_token.scope
        )

        new_refresh_token.to_redis()
        access_token.to_redis()
        refresh_token.delete()

        return jsonify(
            access_token=str(access_token),
            token_type='Bearer',
            expires_in=AccessToken.ttl,
            refresh_token=str(refresh_token)
        )


class UserInfoView(OAuthView):

    def get(self):
        return self._userinfo()

    def post(self):
        return self._userinfo()

    def _userinfo(self):
        user = g.access_token.user
        return jsonify(user.info())


class UserView(DocumentView):
    document_class = User

    def _authorize(self, user):
        if self._no_auth:
            return

        if g.access_token.user_id != user.pk:
            abort(403, "Not authorized to the user")

    def _get_queryset(self):
        qs = super()._get_queryset()
        qs = qs.filter(pk=g.access_token.user_id)
        return qs

    def _create_document(self):
        user = super()._create_document()
        #add logic for creating an account with a social login
        #add logic for email verification
        return user