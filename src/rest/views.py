from flask import g, request
from flask.views import MethodView
from mongoengine.errors import InvalidQueryError, ValidationError
from werkzeug.exceptions import BadRequest, Forbidden


class APIView(MethodView):

    authentication_classes = []
    permission_classes = []

    def dispatch_request(self):
        try:
            self.initial()
            super().dispatch_request()

        except ValidationError as e:
            raise BadRequest(e.to_dict())

        except InvalidQueryError as e:
            raise BadRequest(str(e))

    def initial(self):
        self.perform_authnetication()
        self.check_permissions()

    def get_authenticators(self):
        return [auth() for auth in self.authentication_classes]

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def perform_authnetication(self):
        g.client = None
        for auth in self.get_authenticators():
            g.client = auth.authenticate()
            if g.client is not None:
                break

    def check_permissions(self):
        for permission in self.get_permissions():
            if not permission.has_permission():
                raise Forbidden(permission.message)


