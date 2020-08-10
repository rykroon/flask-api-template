from flask import g, request


SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class BasePermission:
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True


class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(self, view):
        return True


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, view):
        return bool(g.user and g.user.is_authenticated)


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, view):
        return bool(g.user and g.user.is_staff)


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            g.user and g.user.is_authenticated
        )


            










