# -*- coding: utf-8 -*-

import traceback

import flask

from .helpers import render_template


def handle_error(exc):
    tb = traceback.format_exc()
    try:
        code = exc.code
        desc = exc.desc
    except AttributeError:
        code = 500
        desc = exc

    flask.current_app.logger.debug(exc, exc_info=True)

    messages = [f"Error {code}: {desc}", tb]
    return render_template("error.html", messages=messages), code


ERROR_HANDLERS = [(Exception, handle_error)]
