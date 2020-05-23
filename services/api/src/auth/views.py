import os
import traceback
from flask import abort, current_app, g, jsonify, request
from flask.views import MethodView

from auth.decorators import auth
from auth.models import Client
from core.views import ModelView


class ResourceView(ModelView):
    """
        A ModelView more focused on a 'Resource'
        has additional auth related functionality
    """

    def _authorize(self, resource):
        if self._no_auth:
            return

        is_authorized = g.access_token.user_id == resource.user_id
        if not is_authorized:
            abort(403, 'Not authorized to the resource')
    
    def _get_objects(self):
        self.filter['user_id'] = g.access_token.user_id
        return super()._get_objects()

    def _create_object(self):
        resource = super()._create_object()
        resource.user = g.access_token.user
        return resource

    @classmethod
    def as_view(cls, name, use_auth=True, *args, **kwargs):
        view = super().as_view(name, *args, **kwargs)
        if use_auth:
            return auth(view)
        return view


class OAuthView(MethodView):

    def _get_client(self, basic_auth=False):
        if basic_auth:
            client_id = self._get_username()
        else:
            client_id = self._get_param('client_id')

        client = Client.get(client_id)
        if not client:
            abort(401, "Invalid client_id")

        return client

    def _get_param(self, parameter):
        if request.method == 'GET':
            value = request.args.get(parameter)
            
        if request.method == 'POST':
            value = request.form.get(parameter)

        if not value:
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