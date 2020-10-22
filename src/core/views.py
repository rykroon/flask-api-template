from bson.objectid import ObjectId, InvalidId
from flask import abort, current_app, jsonify, request
from flask.views import MethodView


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
