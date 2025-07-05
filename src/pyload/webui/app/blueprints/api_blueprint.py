# -*- coding: utf-8 -*-

import traceback
from ast import literal_eval
from itertools import chain
from logging import getLogger
from urllib.parse import unquote

import flask
from flask.json import jsonify
from pyload import APPID

from ..helpers import clear_session, set_session

bp = flask.Blueprint("api", __name__)
log = getLogger(APPID)


# accepting positional arguments, as well as kwargs via post and get
# @bottle.route(
@bp.route("/api/<func>", methods=["GET", "POST"], endpoint="rpc")
@bp.route("/api/<func>/<args>", methods=["GET", "POST"], endpoint="rpc")
# @apiver_check
def rpc(func, args=""):
    api = flask.current_app.config["PYLOAD_API"]

    if flask.request.authorization:
        user = flask.request.authorization.get("username", "")
        password = flask.request.authorization.get("password", "")
    else:
        user = flask.request.form.get("u", "")
        password = flask.request.form.get("p", "")

    sanitized_user = user.replace("\n", "\\n").replace("\r", "\\r")
    if user:
        user_info = api.check_auth(user, password)
        if user_info:
            s = set_session(user_info)
        else:
            log.error(f"API access failed for user '{sanitized_user}'")
            return jsonify({'error': "Unauthorized"}), 401

    else:
        s = flask.session

    if (
            "role" not in s or
            "perms" not in s or
            not api.is_authorized(func, {"role": s["role"], "permission": s["perms"]})
    ):
        log.error(f"API access failed for user '{sanitized_user}'")
        return jsonify({'error': "Unauthorized"}), 401

    args = args.split(",")
    if len(args) == 1 and not args[0]:
        args = []

    kwargs = {}

    for x, y in chain(flask.request.args.items(), flask.request.form.items()):
        if x not in ("u", "p"):
            kwargs[x] = unquote(y)

    try:
        response = call_api(func, *args, **kwargs)
    except Exception as exc:
        response = jsonify(error=str(exc), traceback=traceback.format_exc()), 500

    return response


def call_api(func, *args, **kwargs):
    api = flask.current_app.config["PYLOAD_API"]

    if func.startswith("_"):
        flask.flash(f"Invalid API call '{func}'")
        return jsonify({'error': "Forbidden"}), 403

    result = getattr(api, func)(
        *[literal_eval(x) for x in args],
        **{x: literal_eval(y) for x, y in kwargs.items()},
    )

    return jsonify(result)


@bp.route("/api/login", methods=["POST"], endpoint="login")
# @apiver_check
def login():
    user = flask.request.form["username"]
    password = flask.request.form["password"]

    api = flask.current_app.config["PYLOAD_API"]
    user_info = api.check_auth(user, password)

    if flask.request.headers.get("X-Forwarded-For"):
        client_ip = flask.request.headers.get("X-Forwarded-For").split(',')[0].strip()
    else:
        client_ip = flask.request.remote_addr

    sanitized_user = user.replace("\n", "\\n").replace("\r", "\\r")
    if not user_info:
        log.error(f"Login failed for user '{sanitized_user}' [CLIENT: {client_ip}]")
        return jsonify(False)

    s = set_session(user_info)
    log.info(f"User '{sanitized_user}' successfully logged in [CLIENT: {client_ip}]")
    flask.flash("Logged in successfully")

    return jsonify(s)


@bp.route("/api/logout", endpoint="logout")
# @apiver_check
def logout():
    s = flask.session
    user = s.get("name")
    clear_session(s)
    if user:
        log.info(f"User '{user}' logged out")
    return jsonify(True)
