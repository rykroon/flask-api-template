from datetime import datetime, timedelta
from flask import Blueprint, abort, current_app, jsonify, make_response, request

from auth.models import AccessToken, AuthorizationCode, RefreshToken, User
from auth.views import OAuthView

bp = Blueprint('token', __name__)


class TokenAPI(OAuthView):

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
        auth_code = AuthorizationCode.get(code)
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

        refresh_token.save()
        access_token.save()
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
        refresh_token = RefreshToken.get(refresh_token)
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

        new_refresh_token.save()
        access_token.save()
        refresh_token.delete()

        return jsonify(
            access_token=str(access_token),
            token_type='Bearer',
            expires_in=AccessToken.ttl,
            refresh_token=str(refresh_token)
        )


token_view = TokenAPI.as_view('token_view')
bp.add_url_rule('/oauth/token', view_func=token_view, methods=['POST'])

