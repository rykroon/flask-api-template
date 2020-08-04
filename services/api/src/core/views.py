from bson.objectid import ObjectId, InvalidId
from flask import abort, current_app, jsonify, request
from flask.views import MethodView



class APIView(MethodView):
    authentication_classes = ()
    permissions_classes = ()
    throttle_classes = ()

    def dispatch_request(self, *args, **kwargs):
        self.intial(*args, **kwargs)

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

    def check_permissions(self, request):
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

    def check_throttles(self, request):
        """
        Check if request should be throttled.
        Raises an appropriate exception if the request is throttled.
        """
        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self):
                return False
                # self.throttled(request, throttle.wait())


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

    def perform_authentication(self):
        pass

    def check_permissions(self):
        pass

    def check_throttles(self):
        pass

    def intial(self, *args, **kwargs):
        pass



class ModelView(MethodView):
    model_class = None

    def dispatch_request(self, *args, **kwargs):
        id = kwargs.pop('id', None)
        if id is not None:
            document = self.retrieve_object(id)
            if document is None:
                abort(404)
            return super().dispatch_request(document, *args, **kwargs)

        return super().dispatch_request(*args, **kwargs)

    def get(self, document=None):
        if document is not None:
            return jsonify(document.to_dict())

        qs = self.get_queryset()
        documents = qs.as_pymongo()
        return jsonify(documents)

    def post(self):
        document = self.create_object()
        return jsonify(document.to_dict()), 201

    def put(self, document):
        document = self.update_object(document)
        return jsonify(document.to_dict())

    def delete(self, document):
        self.delete_object(document)
        return "", 204

    def get_queryset(self):
        return self.__class__.model_class.objects.all()

    def create_object(self):
        data = request.get_json()
        document = self.__class__.model_class(**data)
        document.save()
        return document

    def retrieve_object(self, id):
        return self.__class__.model_class.objects.get(pk=id)

    def update_object(self, document):
        data = request.get_json()
        for key, val in data.items():
            if key in self.__class__.model_class._fields:
                setattr(document, key, val)
        document.save()
        return document

    def delete_object(self, document):
        document.delete()
        return document
