from flask import g, jsonify, request, Blueprint

from rest import APIView, AllowAny, AnonRateThrottle, IsAuthneticated

bp = Blueprint('test', __name__)


class HelloWorldView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def get(self):
        return jsonify({
            'foo': 1,
            'bar': 2,
            'baz': 3
        })


view_func = HelloWorldView.as_view('HelloWorldView')
bp.add_url_rule('/helloworld', view_func=view_func)




