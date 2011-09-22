#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import unquote
from itertools import chain
from traceback import format_exc, print_exc

from bottle import route, request, response, HTTPError

from thrift.protocol.TBase import TBase

from utils import toDict, set_session

from webinterface import PYLOAD

from module.common.json_layer import json_dumps
from module.database.UserDatabase import ROLE

try:
    from ast import literal_eval
except ImportError: # python 2.5
    from module.lib.SafeEval import safe_eval as literal_eval


# convert to format serializable by json
def traverse(data):
    if type(data) == list:
        return [traverse(x) for x in data]
    elif type(data) == dict:
        return dict([(x, traverse(y)) for x, y in data.iteritems()])
    elif isinstance(data, TBase):
        return toDict(data)
    else:
        return data


# accepting positional arguments, as well as kwargs via post and get

@route("/api/:func:args#[a-zA-Z0-9\-_/\"'\[\]%{}]*#")
@route("/api/:func:args#[a-zA-Z0-9\-_/\"'\[\]%{}]*#", method="POST")
def call_api(func, args=""):
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    s = request.environ.get('beaker.session')
    if 'session' in request.POST:
        s = s.get_by_id(request.POST['session'])

    if not s or not s.get("authenticated", False) or s.get("role", -1) != ROLE.ADMIN:
        return HTTPError(401, json_dumps("Unauthorized"))

    args = args.split("/")[1:]
    kwargs = {}

    for x, y in chain(request.GET.iteritems(), request.POST.iteritems()):
        if x == "session": continue
        kwargs[x] = unquote(y)

    try:
        return callApi(func, *args, **kwargs)
    except Exception, e:
        print_exc()
        return HTTPError(500, json_dumps({"error": e.message, "traceback": format_exc()}))


def callApi(func, *args, **kwargs):
    if not hasattr(PYLOAD.EXTERNAL, func) or func.startswith("_"):
        print "Invalid API call", func
        return HTTPError(404, json_dumps("Not Found"))

    result = getattr(PYLOAD, func)(*[literal_eval(x) for x in args],
                                   **dict([(x, literal_eval(y)) for x, y in kwargs.iteritems()]))

    return json_dumps(traverse(result))


#post -> username, password
@route("/api/login", method="POST")
def login():
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    user = request.forms.get("username")
    password = request.forms.get("password")

    info = PYLOAD.checkAuth(user, password)

    if not info:
        return json_dumps(False)

    s = set_session(request, info)

    # get the session id by dirty way, documentations seems wrong
    try:
        sid = s._headers["cookie_out"].split("=")[1].split(";")[0]
        return json_dumps(sid)
    except:
        return json_dumps(True)


@route("/api/logout")
def logout():
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    s = request.environ.get('beaker.session')
    s.delete()
