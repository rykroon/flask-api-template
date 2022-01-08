import logging
from flask import current_app, g, has_app_context, has_request_context


def get_logger():
    if has_request_context():
        return g.logger

    if has_app_context():
        return current_app.logger

    return logging.getLogger('gunicorn.error')
