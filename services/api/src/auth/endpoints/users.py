import os
from flask import Blueprint, abort, current_app, g, jsonify, request

from auth.decorators import auth
from auth.models import User
from core.views import ModelView

bp = Blueprint('users', __name__)


class UserAPI(ModelView):
    model_class = User

    def _authorize(self, user):
        if self._no_auth:
            return

        if g.access_token.user_id != user.pk:
            abort(403, "Not authorized to the user")

    def _get_objects(self):
        self.filter['_id'] = g.access_token.user_id
        return super()._get_objects()

    def _create_object(self):
        user = super()._create_object()
        #add logic for creating an account with a social login
        #add logic for email verification
        return user


user_view = UserAPI.as_view('user_view')
user_view_with_auth = auth(user_view)

bp.add_url_rule('/users', view_func=user_view_with_auth, methods=['GET'])
bp.add_url_rule('/users', view_func=user_view, methods=['POST'])
bp.add_url_rule('/users/<string:id>', view_func=user_view_with_auth, methods=['GET', 'PUT', 'DELETE'])

