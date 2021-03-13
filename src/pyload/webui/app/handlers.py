# -*- coding: utf-8 -*-

import traceback

import flask

from .helpers import render_template


def handle_404(exc):
    flask.current_app.logger.debug("Error 404 - Requested URL: {}".format(flask.request.base_url))
    messages = [f"Error {exc.code}: {exc.description}"]
    return render_template('error.html', messages=messages), 404

def handle_error(exc):
    tb = traceback.format_exc()
    try:
        code = exc.code
        desc = exc.desc
    except AttributeError:
        code = 500
        desc = exc

    flask.current_app.logger.debug(exc, exc_info=True)

    messages = [f"Error {code}: {desc}"]
    messages.extend(tb.split('\n'))
    return render_template("error.html", messages=messages), code


ERROR_HANDLERS = [(Exception, handle_error), (404, handle_404)]
