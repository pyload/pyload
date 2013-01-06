#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import unquote
from itertools import chain
from traceback import format_exc, print_exc

from bottle import route, request, response, HTTPError

from utils import set_session, get_user_api
from webinterface import PYLOAD

from module.Api import ExceptionObject
from module.remote.json_converter import loads, dumps
from module.utils import remove_chars

def add_header(r):
    r.headers.replace("Content-type", "application/json")
    r.headers.append("Cache-Control", "no-cache, must-revalidate")
    r.headers.append("Access-Control-Allow-Origin", "*")  # allow xhr requests

# accepting positional arguments, as well as kwargs via post and get
# only forbidden path symbol are "?", which is used to separate GET data and #
@route("/api/<func><args:re:[^#?]*>")
@route("/api/<func><args:re:[^#?]*>", method="POST")
def call_api(func, args=""):
    add_header(response)

    s = request.environ.get('beaker.session')
    if 'session' in request.POST:
        # removes "' so it works on json strings
        s = s.get_by_id(remove_chars(request.POST['session'], "'\""))

    api = get_user_api(s)
    if not api:
        return HTTPError(403, dumps("Forbidden"))

    if not PYLOAD.isAuthorized(func, api.user):
        return HTTPError(401, dumps("Unauthorized"))

    args = args.split("/")[1:]
    kwargs = {}

    for x, y in chain(request.GET.iteritems(), request.POST.iteritems()):
        if x == "session": continue
        kwargs[x] = unquote(y)

    try:
        return callApi(api, func, *args, **kwargs)
    except ExceptionObject, e:
        return HTTPError(400, dumps(e))
    except Exception, e:
        print_exc()
        return HTTPError(500, dumps({"error": e.message, "traceback": format_exc()}))

# TODO Better error codes on invalid input

def callApi(api, func, *args, **kwargs):
    if not hasattr(PYLOAD.EXTERNAL, func) or func.startswith("_"):
        print "Invalid API call", func
        return HTTPError(404, dumps("Not Found"))

    # TODO: encoding
    result = getattr(api, func)(*[loads(x) for x in args],
                                   **dict([(x, loads(y)) for x, y in kwargs.iteritems()]))

    # null is invalid json response
    if result is None: result = True

    return dumps(result)


#post -> username, password
@route("/api/login", method="POST")
def login():
    add_header(response)

    username = request.forms.get("username")
    password = request.forms.get("password")

    user = PYLOAD.checkAuth(username, password)

    if not user:
        return dumps(False)

    s = set_session(request, user)

    # get the session id by dirty way, documentations seems wrong
    try:
        sid = s._headers["cookie_out"].split("=")[1].split(";")[0]
        return dumps(sid)
    except:
        print "Could not get session"
        return dumps(True)


@route("/api/logout")
@route("/api/logout", method="POST")
def logout():
    add_header(response)

    s = request.environ.get('beaker.session')
    s.delete()

    return dumps(True)
