# -*- coding: utf-8 -*-

import flask
from .helpers import render_error


def handle_error(exc):
    try:
        code = exc.code
    except AttributeError:
        code = 500
        
    flask.current_app.logger.debug(exc, exc_info=True)
    
    messages = ["Sorry, something went wrong... :(", f"Error {code}: {exc}"]
    return render_error(messages), code
            
            
ERROR_HANDLERS = [(Exception, handle_error)]
