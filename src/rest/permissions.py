from flask import g, request


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class BasePermission:
    message = ''

    def has_permission(self):
        raise NotImplementedError

    def has_object_permission(self, obj):
        raise NotImplementedError


class AllowAny(BasePermission):

    def has_permission(self):
        return True


class IsAuthneticated(BasePermission):
    message = 'Authenticated clients only.'

    def has_permission(self):
        return g.client is not None


class IsAuthneticatedOrReadOnly(BasePermission):
    message = 'Authenticated clients or read only.'

    def has_permission(self):
        return request.method in SAFE_METHODS or g.client is not None
