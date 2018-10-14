# -*- coding: utf-8 -*-

import traceback
from ast import literal_eval
from itertools import chain
from urllib.parse import unquote

import bottle

from pyload.api import BaseObject
from pyload.plugins.utils import json  # change to core utils
from pyload.webui import PYLOAD
from pyload.webui.utils import apiver_check, set_session, toDict


# json encoder that accepts TBase objects
class TBaseEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseObject):
            return toDict(o)
        return json.JSONEncoder.default(self, o)


# accepting positional arguments, as well as kwargs via post and get
@bottle.route(r"/api/<apiver>/<func><args:re:[a-zA-Z0-9\-_/\"\'\[\]%{},]*>")
@bottle.route(
    r"/api/<apiver>/<func><args:re:[a-zA-Z0-9\-_/\"\'\[\]%{},]*>", method="POST"
)
@apiver_check
def call_api(func, args=""):
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    if "u" in request.POST and "p" in request.POST:
        info = PYLOAD.checkAuth(request.POST["u"], request.POST["p"])
        if info:
            if not PYLOAD.isAuthorized(
                func, {"role": info["role"], "permission": info["permission"]}
            ):
                return bottle.HTTPError(401, json.dumps("Unauthorized"))

        else:
            return bottle.HTTPError(403, json.dumps("Forbidden"))

    else:
        s = request.environ.get("beaker.session")
        if "session" in request.POST:
            s = s.get_by_id(request.POST["session"])

        if not s or not s.get("authenticated", False):
            return bottle.HTTPError(403, json.dumps("Forbidden"))

        if not PYLOAD.isAuthorized(func, {"role": s["role"], "permission": s["perms"]}):
            return bottle.HTTPError(401, json.dumps("Unauthorized"))

    args = args.split("/")[1:]
    kwargs = {}

    for x, y in chain(iter(request.GET.items()), iter(request.POST.items())):
        if x in ("u", "p", "session"):
            continue
        kwargs[x] = unquote(y)

    try:
        return callApi(func, *args, **kwargs)
    except Exception as e:
        traceback.print_exc()
        return bottle.HTTPError(
            500, json.dumps({"error": e.message, "traceback": traceback.format_exc()})
        )


def callApi(func, *args, **kwargs):
    if not hasattr(PYLOAD.EXTERNAL, func) or func.startswith("_"):
        print("Invalid API call", func)
        return bottle.HTTPError(404, json.dumps("Not Found"))

    result = getattr(PYLOAD, func)(
        *[literal_eval(x) for x in args],
        **{x: literal_eval(y) for x, y in kwargs.items()},
    )

    # null is invalid json  response
    return json.dumps(result or True, cls=TBaseEncoder)


# post -> username, password
@bottle.route(r"/api/<apiver>/login", method="POST")
@apiver_check
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
    except Exception:
        return json.dumps(True)


@bottle.route(r"/api/<apiver>/logout")
@apiver_check
def logout():
    response.headers.replace("Content-type", "application/json")
    response.headers.append("Cache-Control", "no-cache, must-revalidate")

    s = request.environ.get("beaker.session")
    s.delete()
