from bson.objectid import ObjectId, InvalidId
from flask import abort, current_app, jsonify, request
from flask.views import MethodView


class DocumentView(MethodView):
    document_class = None

    def dispatch_request(self, *args, **kwargs):
        id = kwargs.pop('id', None)
        if id is not None:
            document = self._get_document(id)
            if document is None:
                abort(404)
            return super().dispatch_request(document, *args, **kwargs)

        return super().dispatch_request(*args, **kwargs)

    def get(self, document=None):
        if document is not None:
            return jsonify(document.to_dict())

        qs = self._get_queryset()
        documents = list(qs._cursor)
        return jsonify(documents)

    def post(self):
        document = self._create_document()
        return jsonify(document.to_dict()), 201

    def put(self, document):
        document = self._update_document(document)
        return jsonify(document.to_dict())

    def delete(self, document):
        self._destroy_document(document)
        return "", 204

    def _get_document(self, id):
        return self.__class__.document_class.objects.get(pk=id)

    def _get_queryset(self):
        query_args = request.args.to_dict()
        
        fields = query_args.pop('fields', "")
        if fields:
            fields = fields.split(',')

        sort = query_args.pop('sort', "")
        if sort:
            sort = sort.split(',')

        limit = int(query_args.pop('limit', 0))
        offset = int(query_args.pop('offset', 0))

        qs = self.__class__.document_class.objects.filter(**query_args)
        if fields:
            qs = qs.only(*fields)

        if sort:
            qs = qs.order_by(**sort)

        if limit:
            qs = qs.limit(limit)

        if offset:
            qs = qs.skip(offset)

        return qs

    def _create_document(self):
        data = request.get_json()
        document = self.__class__.document_class(**data)
        document.save()
        return document

    def _update_document(self, document):
        data = request.get_json()
        for key, val in data.items():
            if key in self.__class__.document_class._fields:
                setattr(document, key, val)
        document.save()
        return document

    def _destroy_document(self, document):
        document.delete()
        return document
