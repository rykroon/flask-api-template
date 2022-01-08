from functools import wraps
from flask import g, request
from werkzeug.exceptions import Forbidden


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class BasePermission:
    def has_permission(self):
        raise NotImplementedError


class AllowAny(BasePermission):
    def has_permission(self):
        return True


class IsAuthenticated(BasePermission):
    def has_permission(self):
        return bool(g.client)


class IsAdmin(BasePermission):
    def has_permission(self):
        return bool(g.client) and g.client.is_admin


class IsAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self):
        return bool(request.method in SAFE_METHODS) or bool(g.client)


def permission_decorator_factory(permission_class, **permission_kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            perm = permission_class(**permission_kwargs)
            if not perm.has_permission():
                raise Forbidden
            return func(*args, **kwargs)
        return wrapper
    return decorator


allow_any = permission_decorator_factory(AllowAny)
is_authenticated = permission_decorator_factory(IsAuthenticated)
is_admin = permission_decorator_factory(IsAdmin)
is_authenticated_or_read_only = permission_decorator_factory(IsAuthenticatedOrReadOnly)
