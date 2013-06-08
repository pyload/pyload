#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import unquote
from itertools import chain
from traceback import format_exc, print_exc

from bottle import route, request, response, HTTPError, parse_auth

from utils import set_session, get_user_api
from webinterface import PYLOAD

from module.Api import ExceptionObject
from module.remote.json_converter import loads, dumps
from module.utils import remove_chars

def add_header(r):
    r.headers.replace("Content-type", "application/json")
    r.headers.append("Cache-Control", "no-cache, must-revalidate")
    r.headers.append("Access-Control-Allow-Origin", request.get_header('Origin', '*'))
    r.headers.append("Access-Control-Allow-Credentials", "true")

# accepting positional arguments, as well as kwargs via post and get
# only forbidden path symbol are "?", which is used to separate GET data and #
@route("/api/<func><args:re:[^#?]*>")
@route("/api/<func><args:re:[^#?]*>", method="POST")
def call_api(func, args=""):
    add_header(response)

    s = request.environ.get('beaker.session')
    # Accepts standard http auth
    auth = parse_auth(request.get_header('Authorization', ''))
    if 'session' in request.POST or 'session' in request.GET:
        # removes "' so it works on json strings
        s = s.get_by_id(remove_chars(request.params.get('session'), "'\""))
    elif auth:
        user = PYLOAD.checkAuth(auth[0], auth[1], request.environ.get('REMOTE_ADDR', None))
        # if auth is correct create a pseudo session
        if user: s = {'uid': user.uid}

    api = get_user_api(s)
    if not api:
        return HTTPError(401, dumps("Unauthorized"), **response.headers)

    if not PYLOAD.isAuthorized(func, api.user):
        return HTTPError(403, dumps("Forbidden"), **response.headers)

    if not hasattr(PYLOAD.EXTERNAL, func) or func.startswith("_"):
        print "Invalid API call", func
        return HTTPError(404, dumps("Not Found"), **response.headers)

    # TODO: possible encoding
    # TODO Better error codes on invalid input

    args = [loads(unquote(arg)) for arg in args.split("/")[1:]]
    kwargs = {}

    # accepts body as json dict
    if request.json:
        kwargs = request.json

    # convert arguments from json to obj separately
    for x, y in chain(request.GET.iteritems(), request.POST.iteritems()):
        if not x or not y or x == "session": continue
        kwargs[x] = loads(unquote(y))

    try:
        result = getattr(api, func)(*args, **kwargs)
        # null is invalid json response
        if result is None: result = True
        return dumps(result)

    except ExceptionObject, e:
        return HTTPError(400, dumps(e), **response.headers)
    except Exception, e:
        print_exc()
        return HTTPError(500, dumps({"error": e.message, "traceback": format_exc()}), **response.headers)


@route("/api/login")
@route("/api/login", method="POST")
def login():
    add_header(response)

    username = request.params.get("username")
    password = request.params.get("password")

    user = PYLOAD.checkAuth(username, password, request.environ.get('REMOTE_ADDR', None))

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
