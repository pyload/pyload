#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bottle import route, request, response, HTTPError, redirect

from webinterface import PROJECT_DIR, SETUP, env
from utils import render_to_response

def setup_required(func):
    def _view(*args, **kwargs):

        # setup needs to be running
        if SETUP is None:
            redirect("/nopermission")

        return func(*args, **kwargs)
    return _view


@route("/setup")
@setup_required
def setup():
    
    return render_to_response('setup.html')
