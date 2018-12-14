# -*- coding: utf-8 -*-

import flask
from .helpers import render_base


def handle_error(exc):
    try:
        code = exc.code
        desc = exc.desc
    except AttributeError:
        code = 500
        desc = exc
        
    flask.current_app.logger.debug(exc, exc_info=True)
    
    messages = ["Sorry, something went wrong... :(", f"Error {code}: {desc}"]
    return render_base(messages), code
            
            
ERROR_HANDLERS = [(Exception, handle_error)]
