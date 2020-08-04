from flask import g, request


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class BasePermission:
    def has_permission(self):
        raise NotImplementedError

    def has_object_permission(self, obj):
        raise NotImplementedError


class Nobody(BasePermission):
    def has_object_permission(self, obj):
        return False


class Everybody(BasePermission):
    def has_object_permission(self, obj):
        return True


class Owner(BasePermission):
    def has_object_permission(self, obj):
        return g.user == obj.owner


class OwnerOrReadOnly(BasePermission):
    def has_object_permission(self, obj):
        if g.user == obj.owner:
            return True

        return request.method in SAFE_METHODS

            










