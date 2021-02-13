from flask.views import MethodView
from mongoengine.errors import InvalidQueryError, ValidationError
from werkzeug.exceptions import BadRequest


class ResourceView(MethodView):

    def dispatch_request(self):
        try:
            super().dispatch_request()
        
        except ValidationError as e:
            raise BadRequest(e.to_dict())

        except InvalidQueryError as e:
            raise BadRequest(str(e))
