#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time

from bottle import route, request, response, HTTPError, redirect

from webinterface import PROJECT_DIR, SETUP

from utils import add_json_header

def setup_required(func):
    def _view(*args, **kwargs):
        # setup needs to be running
        if SETUP is None:
            redirect("/nopermission")

        return func(*args, **kwargs)
    return _view

# setup will close after inactivity
TIMEOUT = 15
timestamp = time()

@route("/setup")
@setup_required
def setup():
    pass # TODO
