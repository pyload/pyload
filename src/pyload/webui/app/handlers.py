# -*- coding: utf-8 -*-

import flask
from .helpers import render_error


def handle_error(exc):
    code = 500
    try:
        code = exc.code
    except AttributeError:
        pass
        
    flask.current_app.logger.debug(exc, exc_info=True)
    
    messages = ["Sorry, something went wrong... :(", str(exc)]
    return render_error(messages), code
            
            
ERROR_HANDLERS = [(Exception, handle_error)]
