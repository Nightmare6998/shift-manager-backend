from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.extensions import db


def error_response(status, error, message, details=None):
    return jsonify(error=error, message=message, details=details or {}), status


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def http_error(error):
        names = {400: "validation_error", 401: "authentication_error",
                 403: "authorization_error", 404: "not_found", 405: "method_not_allowed"}
        response, status = error_response(error.code, names.get(error.code, "http_error"),
                                          error.description)
        if error.code == 405:
            response.headers["Allow"] = ", ".join(error.valid_methods or [])
        return response, status

    @app.errorhandler(Exception)
    def server_error(error):
        db.session.rollback()
        app.logger.exception("Request failed")
        return error_response(500, "server_error", "Something went wrong.")
