# -*- coding: utf-8 -*-

import itertools
import traceback
import urllib

import SafeEval
import bottle

from pyload.Api import BaseObject
from pyload.utils import json, json_dumps
from pyload.webui import PYLOAD
from pyload.webui.App.utils import toDict, set_session


# json encoder that accepts TBase objects
class TBaseEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, BaseObject):
            return toDict(o)
        return json.JSONEncoder.default(self, o)


# accepting positional arguments, as well as kwargs via post and get
@bottle.route('/api/<func><args:re:[a-zA-Z0-9\-_/\"\'\[\]%{},]*>')
@bottle.route('/api/<func><args:re:[a-zA-Z0-9\-_/\"\'\[\]%{},]*>', method='POST')
def call_api(func, args=""):
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    s = request.environ.get('beaker.session')
    if 'session' in request.POST:
        s = s.get_by_id(request.POST['session'])

    if not s or not s.get("authenticated", False):
        return bottle.HTTPError(403, json_dumps("Forbidden"))

    if not PYLOAD.isAuthorized(func, {"role": s['role'], "permission": s['perms']}):
        return bottle.HTTPError(401, json_dumps("Unauthorized"))

    args = args.split("/")[1:]
    kwargs = {}

    for x, y in itertools.chain(request.GET.iteritems(), request.POST.iteritems()):
        if x == "session":
            continue
        kwargs[x] = urllib.unquote(y)

    try:
        return callApi(func, *args, **kwargs)
    except Exception, e:
        traceback.print_exc()
        return bottle.HTTPError(500, json_dumps({"error": e.message, "traceback": traceback.format_exc()}))


def callApi(func, *args, **kwargs):
    if not hasattr(PYLOAD.EXTERNAL, func) or func.startswith("_"):
        print "Invalid API call", func
        return bottle.HTTPError(404, json_dumps("Not Found"))

    result = getattr(PYLOAD, func)(*[SafeEval.const_eval(x) for x in args],
                                   **dict((x, SafeEval.const_eval(y)) for x, y in kwargs.iteritems()))

    # null is invalid json  response
    return json_dumps(result or True, cls=TBaseEncoder)


# post -> username, password
@bottle.route('/api/login', method='POST')
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
        sid = s._headers['cookie_out'].split("=")[1].split(";")[0]
        return json_dumps(sid)
    except Exception:
        return json_dumps(True)


@bottle.route('/api/logout')
def logout():
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    s = request.environ.get('beaker.session')
    s.delete()
