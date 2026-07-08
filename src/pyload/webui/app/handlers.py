import flask
from flask_wtf.csrf import CSRFError

from .helpers import render_template


def handle_404_error(exc):
    flask.current_app.logger.debug("Error 404 - Requested URL: {}".format(flask.request.base_url))
    messages = [f"Error {exc.code}: {exc.description}"]
    return render_template('error.html', messages=messages), 404

def handle_exception_error(exc):
    flask.current_app.logger.debug(exc, exc_info=True)
    return render_template("error.html", messages=["Error: exception occurred while processing the request"]), 500


def handle_csrf_error(exc):
    flask.current_app.logger.debug(f"CSRF Error: {exc.description}")
    if flask.request.headers.get("Content-Type") == "application/json":
        return flask.jsonify({"error": "CSRF token is invalid"}), 400
    else:
        return "CSRF token is invalid", 400


ERROR_HANDLERS = [
    (CSRFError, handle_csrf_error),
    (404, handle_404_error),
    (Exception, handle_exception_error)
]
