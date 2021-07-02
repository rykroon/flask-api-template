from flask import g
from auth.authentication.models import UnauthenticatedUser


class AuthenticationMiddleware:
    def __init__(self, authentication_classes):
        self.authentication_classes = authentication_classes

    def __call__(self):
        for auth in self.get_authenticators():
            g.user = auth.authenticate()
            if g.user is not None:
                return

        g.user = UnauthenticatedUser()

    def get_authenticators(self):
        return [auth() for auth in self.authentication_classes]