#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import unquote
from itertools import chain
from traceback import format_exc, print_exc

from bottle import route, request, response, HTTPError

from utils import toDict, set_session
from webinterface import PYLOAD

from module.common.json_layer import json
from module.lib.SafeEval import const_eval as literal_eval
from module.Api import BaseObject

# json encoder that accepts TBase objects
class TBaseEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, BaseObject):
            return toDict(o)
        return json.JSONEncoder.default(self, o)


# accepting positional arguments, as well as kwargs via post and get

@route("/api/:func:args#[a-zA-Z0-9\-_/\"'\[\]%{}]*#")
@route("/api/:func:args#[a-zA-Z0-9\-_/\"'\[\]%{}]*#", method="POST")
def call_api(func, args=""):
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    if 'u' in request.POST and 'p' in request.POST:
        info = PYLOAD.checkAuth(request.POST['u'], request.POST['p'])
        if info:
            if not PYLOAD.isAuthorized(func, {"role": info["role"], "permission": info["permission"]}):
                return HTTPError(401, json.dumps("Unauthorized"))

        else:
            return HTTPError(403, json.dumps("Forbidden"))

    else:
        s = request.environ.get('beaker.session')
        if 'session' in request.POST:
            s = s.get_by_id(request.POST['session'])

        if not s or not s.get("authenticated", False):
            return HTTPError(403, json.dumps("Forbidden"))

        if not PYLOAD.isAuthorized(func, {"role": s["role"], "permission": s["perms"]}):
            return HTTPError(401, json.dumps("Unauthorized"))

    args = args.split("/")[1:]
    kwargs = {}

    for x, y in chain(request.GET.iteritems(), request.POST.iteritems()):
        if x in ("u", "p", "session"): continue
        kwargs[x] = unquote(y)

    try:
        return callApi(func, *args, **kwargs)
    except Exception, e:
        print_exc()
        return HTTPError(500, json.dumps({"error": e.message, "traceback": format_exc()}))


def callApi(func, *args, **kwargs):
    if not hasattr(PYLOAD.EXTERNAL, func) or func.startswith("_"):
        print "Invalid API call", func
        return HTTPError(404, json.dumps("Not Found"))

    result = getattr(PYLOAD, func)(*[literal_eval(x) for x in args],
                                   **dict([(x, literal_eval(y)) for x, y in kwargs.iteritems()]))

    # null is invalid json  response
    if result is None: result = True

    return json.dumps(result, cls=TBaseEncoder)


#post -> username, password
@route("/api/login", method="POST")
def login():
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    user = request.forms.get("username")
    password = request.forms.get("password")

    info = PYLOAD.checkAuth(user, password)

    if not info:
        return json.dumps(False)

    s = set_session(request, info)

    # get the session id by dirty way, documentations seems wrong
    try:
        sid = s._headers["cookie_out"].split("=")[1].split(";")[0]
        return json.dumps(sid)
    except:
        return json.dumps(True)


@route("/api/logout")
def logout():
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    s = request.environ.get('beaker.session')
    s.delete()
