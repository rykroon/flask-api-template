from bson.objectid import ObjectId, InvalidId
from flask import abort, current_app, g, jsonify, request
from flask.views import MethodView
from core import exceptions



class APIView(MethodView):
    authentication_classes = ()
    permission_classes = ()
    throttle_classes = ()

    def dispatch_request(self, *args, **kwargs):
        try:
            self.initial(*args, **kwargs)
            response = super().dispatch_request(*args, **kwargs)
        except Exception as exc:
            current_app.logger.info(type(exc))
            response = jsonify(error=str(exc))
            #response = self.handle_exception(exc)

        self.response = response #self.finalize_response(response)
        return self.response


    def check_object_permissions(self, obj):
        """
            Check if the request should be permitted for a given object.
            Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                return False
                # self.permission_denied(
                #     request, message=getattr(permission, 'message', None)
                # )

    def check_permissions(self):
        """
            Check if the request should be permitted.
            Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                return False
                # self.permission_denied(
                #     request, message=getattr(permission, 'message', None)
                # )

    def check_throttles(self):
        """
            Check if request should be throttled.
            Raises an appropriate exception if the request is throttled.
        """
        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self):
                self.throttled(throttle.wait())

    def get_authenticators(self):
        """
            Instantiates and returns the list of authenticators that this view can use.
        """
        return [auth() for auth in self.authentication_classes]

    def get_permissions(self):
        """
            Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def get_throttles(self):
        """
            Instantiates and returns the list of throttles that this view uses.
        """
        return [throttle() for throttle in self.throttle_classes]

    def initial(self, *args, **kwargs):
        """
            Runs anything that needs to occur prior to calling the method handler.
        """
        # Ensure that the incoming request is permitted
        self.perform_authentication()
        self.check_permissions()
        self.check_throttles()

    def not_authenticated(self):
        """
            Set authenticator, user & authtoken representing an unauthenticated request.
            Defaults are None, AnonymousUser & None.
        """
        g.user = None
        g.auth = None
        g.authenticator = None

    def perform_authentication(self):
        """
            Attempt to authenticate the request using each authentication instance
            in turn.
        """
        g.user = None
        g.auth = None

        for authenticator in self.get_authenticators():
            try:
                user_auth_tuple = authenticator.authenticate(self)
            except exceptions.APIException:
                self.not_authenticated()
                raise

            if user_auth_tuple is not None:
                g.authenticator = authenticator
                g.user, g.auth = user_auth_tuple
                return

        self.not_authenticated()

    def throttled(self, wait):
        """
            If request is throttled, determine what kind of exception to raise.
        """
        raise exceptions.Throttled(wait)


class GenericAPIView(APIView):
    
    def get_queryset(self):
        pass

    def get_object(self):
        pass

