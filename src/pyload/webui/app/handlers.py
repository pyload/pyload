# -*- coding: utf-8 -*-

import traceback
import sys
import flask
from .helpers import render_template


def handle_error(exc):
    try:
        code = exc.code
        desc = exc.desc
        tb = None
    except AttributeError:
        code = 500
        desc = exc
        tb = traceback.format_exception(*sys.exc_info())
        
    flask.current_app.logger.debug(exc, exc_info=True)
    
    messages = [f"Error {code}: {desc}", tb]
    return render_template("error.html", messages=messages), code
            
            
ERROR_HANDLERS = [(Exception, handle_error)]
