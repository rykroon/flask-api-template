from flask import request


class BaseUser:

    @property
    def identifier(self):
        raise NotImplementedError

    @property
    def is_authenticated(self):
        raise NotImplementedError

    @property
    def is_admin(self):
        raise NotImplementedError


class SimpleUser(BaseUser):

    @property
    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        return False


class UnauthenticatedUser(BaseUser):

    @property
    def identifier(self):
        if request.access_route:
            return ''.join(request.access_route)
        return request.remote_addr

    @property
    def is_authenticated(self):
        return False

    @property
    def is_admin(self):
        return False