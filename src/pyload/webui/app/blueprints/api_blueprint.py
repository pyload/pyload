# -*- coding: utf-8 -*-

import json
import traceback
from ast import literal_eval
from itertools import chain
from urllib.parse import unquote

import flask
from flask.json import jsonify

from pyload.core.api import BaseObject
from pyload.webui.app.helpers import clear_session, set_session, toDict

bp = flask.Blueprint("api", __name__, url_prefix="/api")


# accepting positional arguments, as well as kwargs via post and get
# @bottle.route(
# r"/api/<func><args:re:[a-zA-Z0-9\-_/\"\'\[\]%{},]*>")
@bp.route(r"/<func>/<path:args>", methods=["GET", "POST"])
# @apiver_check
def call_api(func, args=""):
    api = flask.current_app.config["PYLOAD_API"]

    # TODO: change u/p to username/password
    if "u" in flask.request.form and "p" in flask.request.form:
        info = api.checkAuth(flask.request.form["u"], flask.request.form["p"])
        if info:
            if not api.isAuthorized(
                func, {"role": info["role"], "permission": info["permission"]}
            ):
                return "Unauthorized", 401

        else:
            return "Forbidden", 403

    else:
        return "Unauthorized", 401
        # s = flask.session
        # if "session" in flask.request.form:
            # s = s.get_by_id(flask.request.form["session"])

        # if not s or not s.get("authenticated", False):
            # return "Forbidden", 403

        # if not api.isAuthorized(func, {"role": s["role"], "permission": s["perms"]}):
            # return "Unauthorized", 401

    args = args.split("/")
    kwargs = {}

    for x, y in chain(
        iter(flask.request.args.items()), iter(flask.request.form.items())
    ):
        if x in ("u", "p", "session"):
            continue
        kwargs[x] = unquote(y)

    try:
        return callApi(func, *args, **kwargs)
    except Exception as e:
        return (
            jsonify(
                {"error": e.message, "traceback": traceback.format_exc()}
            ),
            500,
        )


def callApi(func, *args, **kwargs):
    api = flask.current_app.config["PYLOAD_API"]

    if not hasattr(api.EXTERNAL, func) or func.startswith("_"):
        print("Invalid API call", func)
        return "Not Found", 404

    result = getattr(api, func)(
        *[literal_eval(x) for x in args],
        **{x: literal_eval(y) for x, y in kwargs.items()},
    )

    # convert TBase objects
    if isinstance(result, BaseObject):
        result = toDict(result)
            
    # null is invalid json response
    return jsonify(result or True)


# post -> username, password
@bp.route(r"/login", methods=["POST"])
# @apiver_check
def login():
    user = flask.request.form.get("username")
    password = flask.request.form.get("password")

    api = flask.current_app.config["PYLOAD_API"]
    info = api.checkAuth(user, password)

    if not info:
        return jsonify(False)

    user = User(info['id'])
    login_user(user)
    
    flask.flash('Logged in successfully.')
    
    return jsonify(True)
    
    # s = set_session(info)

    # get the session id by dirty way, documentations seems wrong
    # try:
        # sid = s.headers["cookie_out"].split("=")[1].split(";")[0]
        # return jsonify(sid)
    # except Exception:
        # return jsonify(True)


@bp.route(r"/logout")
# @apiver_check
def logout():
    logout_user()
    clear_session()
    return jsonify(True)
