#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import route, request, response, HTTPError

from webinterface import PROJECT_DIR, SETUP, env
from utils import render_to_response


@route("/setup")
def setup():
    
    return render_to_response('setup.html')
