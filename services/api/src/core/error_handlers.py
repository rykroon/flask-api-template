from flask import jsonify


def bad_request(e):
    return jsonify(
        error='bad_request',
        error_description=str(e)
    ), 400


def unauthorized(e):
    return jsonify(
        error='unauthorized',
        error_description=str(e) 
    ), 401


def forbidden(e):
    return jsonify(
        error='forbidden',
        error_description=str(e)
    ), 403 


def not_found(e):
    return jsonify(
        error='not_found',
        error_description=str(e)
    ), 404


def method_not_allowed(e):
    return jsonify(
        error='method_not_allowed',
        error_description=str(e)
    ), 405


def internal_server_error(e):
    return jsonify(
        error='internal_server_error',
        error_description=str(e)
    ), 500


error_handlers = {
    400: bad_request, 
    401: unauthorized, 
    403: forbidden, 
    404: not_found, 
    405: method_not_allowed, 
    500: internal_server_error
}
