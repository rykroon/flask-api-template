from flask import jsonify
from werkzeug.exceptions import HTTPException, InternalServerError


def handle_http_exception(e: HTTPException):
    return jsonify(name=e.name, description=e.description), e.code


def handle_server_error(e: Exception):
    ise = InternalServerError(original_exception=e)
    return jsonify(name=ise.name, description=ise.description), ise.code


error_handlers = {
    HTTPException: handle_http_exception,
    Exception: handle_server_error,
}
