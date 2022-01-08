from flask.views import MethodView
from utils.auth import is_authenticated


class APIView(MethodView):
    decorators = [is_authenticated]
