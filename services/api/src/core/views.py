import os
import traceback
import types

from bson.objectid import ObjectId, InvalidId
from flask import abort, current_app, jsonify, request
from flask.views import MethodView
from pymongo import ASCENDING, DESCENDING

from core.db import mongo
from core.descriptors import CollectionDescriptor


class BaseView(MethodView):
    def dispatch_request(self, *args, **kwargs):
        try:
            #make sure POST and PUT requests are JSON
            if request.method in ('POST', 'PUT'):
                request.get_json() is not None or abort(400, "Invalid JSON format")

            # if the kwargs contain an `id` then check for an object with that id
            id = kwargs.pop('id', None)
            if id is not None:
                obj = self._get_object_by_id(id)          
                self._authorize(obj)
                return super().dispatch_request(obj, *args, **kwargs)

            # For GET requests that are not for a specific instance, get 
            # attributes from the query args
            if request.method == 'GET':
                self._get_query_args()

            return super().dispatch_request(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            raise e

    @property
    def _no_auth(self):
        if os.getenv('FLASK_ENV') == 'development':
            if os.getenv('NO_AUTH') == 'true':
                return True
        return False

    def _authorize(self, obj):
        """
            if object is unauthorized then abort with 403
        """
        return NotImplemented
        
    def _get_object_by_id(self, id):
        """
            :return: an object with the given id or None
        """
        raise NotImplementedError

    def _get_objects(self):
        """
            :return: A list of objects
        """
        raise NotImplementedError

    def _get_query_args(self):
        query_args = request.args.to_dict()
        self.fields = query_args.pop('fields', None)
        if self.fields:
            self.fields = self.fields.split(',')
        
        self.sort = query_args.pop('sort', None)
        if self.sort:
            self.sort = self.sort.split(',')

        self.limit = int(query_args.pop('limit', 0))
        self.offset = int(query_args.pop('offset', 0))
        self.filter = query_args

    def _create_object(self):
        """
           :return: a new object 
        """
        raise NotImplementedError

    def _update_object(self, obj):
        """
            :return: The updated object
        """
        raise NotImplementedError


class DocumentView(BaseView):
    client = mongo
    collection_name = None
    database_name = None
    collection = CollectionDescriptor()
    allowed_fields = ()

    def get(self, document=None):
        if document:
            return jsonify(document)
        return jsonify(self._get_objects())

    def post(self):
        document = self._create_object()
        return jsonify(document), 201

    def put(self, document):
        document = self._update_object(document)
        return jsonify(document)

    def delete(self, document):
        self.__class__.collection.delete_one({'_id': document['_id']})
        return jsonify(document)

    def _get_object_by_id(self, id):
        try:
            object_id = ObjectId(id)
        except InvalidId:
            object_id = id

        document = self.__class__.collection.find_one({'_id': object_id})
        if document is None:
            abort(404)
        return document

    def _get_objects(self):
        cursor = self.__class__.collection.find(self._filter, self._fields)
        if self.sort:
            sort = [(field[1:], DESCENDING) if field.startswith('-') else (field, ASCENDING) for field in self.sort]
            cursor.sort(sort)

        if self.limit:
            cursor.limit(self.limit)

        if self.offset:
            cursor.skip(self.offset)

        return list(cursor)

    def _create_object(self):
        document = request.get_json()

        for field in document:
            if field not in self.__class__.allowed_fields:
                abort(400, "Invalid field '{}'".format(field))

        self.__class__.collection.insert_one(document)
        return document

    def _update_object(self, document):
        data = request.get_json()

        for field in data:
            if field not in self.__class__.allowed_fields:
                abort(400, "Invalid field '{}'".format(field))

        document.update(data)
        self.__class__.collection.update_one(
            {'_id': document['_id']}, 
            {'$set': document}
        )
        return document


class ModelView(BaseView):
    """
        A class designed to turn a Model into a View
    """
    model_class = None

    def get(self, instance=None):
        if instance:
            return jsonify(instance.to_dict())
        return jsonify(self._get_objects())

    def post(self):
        instance = self._create_object()
        instance.save()
        return jsonify(instance.to_dict()), 201

    def put(self, instance):
        instance = self._update_object(instance)
        instance.save()
        return jsonify(instance.to_dict())

    def delete(self, instance):
        instance.delete()
        return jsonify(instance.to_dict())

    def _get_object_by_id(self, id):
        instance = self.__class__.model_class.query.get(id)
        if instance is None:
            abort(404, "'{}' not found".format(self.__class__.model_class.__name__))
        return instance

    def _get_objects(self):
        q = self.__class__.model_class.query
        if self.sort:
            q.sort(*self.sort)

        if self.limit:
            q.limit(self.limit)

        if self.offset:
            q.offset(self.offset)

        if self.fields:
            q.values(*self.fields)
        else:
            q.values()

        return q.all()

    def _create_object(self):
        data = request.get_json()

        try:
            instance = self.__class__.model_class(**data)

        except Exception as e:
            current_app.logger.error(traceback.format_exc())
            abort(400, e)
        
        return instance

    def _update_object(self, instance):
        data = request.get_json()
        
        for attr, value in data.items():
            
            #make sure private fields cannot get overridden
            if attr.startswith('_'):
                abort(400, "Attribute '{}' cannot be updated".format(attr))

            #make sure methods do not get overridden
            if hasattr(instance, attr):
                if type(getattr(instance, attr)) == types.MethodType:
                    abort(400, "Attribute '{}' cannot be updated".format(attr))

            setattr(instance, attr, value)

        return instance



