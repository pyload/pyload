# -*- coding: utf-8 -*-
import json
import traceback
from ast import literal_eval
from itertools import chain
from logging import getLogger
from typing import Any
from urllib.parse import unquote

import flask
from flask.json import jsonify

from pyload import APPID
from ..api_docs.openapi_specification_generator import OpenAPISpecificationGenerator
from ..helpers import clear_session, set_session, render_template

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

    if func.startswith("_"):
        flask.flash(f"Invalid API call '{func}'")
        return jsonify({'error': "Forbidden"}), 403

    # get path parameters
    args = args.split(",")
    if len(args) == 1 and not args[0]:
        args = []

    # get query parameters
    kwargs = {}
    for x, y in chain(flask.request.args.items(), flask.request.form.items()):
        if x not in ("u", "p"):
            kwargs[x] = unquote(y)

    try:
        if flask.request.mimetype == "application/json":
            # get JSON request body
            json_request_body = flask.request.get_json()
            response = jsonify(getattr(api, func)(**json_request_body))
        elif flask.request.mimetype == "multipart/form-data":
            # get uploaded file - currently only single file upload possible
            name, file = next(iter(flask.request.files.items()))
            response = jsonify(getattr(api, func)(
                **{x: _parse_parameter(y) for x, y in kwargs.items()},
                **{name: file.read()}
            ))
        else:
            response = jsonify(getattr(api, func)(
                *[_parse_parameter(x) for x in args],
                **{x: _parse_parameter(y) for x, y in kwargs.items()},
            ))
    except Exception as exc:
        response = jsonify(error=str(exc), traceback=traceback.format_exc()), 500

    return response


def _parse_parameter(param: str) -> Any:
    if param == "true":
        return True
    elif param == "false":
        return False
    else:
        try:
            return literal_eval(param)
        except ValueError:
            # this is required to allow string parameters without extra quotes
            return literal_eval("\"" + param + "\"")


@bp.route("/api/openapi.json", methods=["GET"])
def api_docs():
    """Return OpenAPI specification JSON"""
    openapi_spec = OpenAPISpecificationGenerator(api=flask.current_app.config["PYLOAD_API"]).generate_openapi_json()
    return openapi_spec

@bp.route("/api/docs", methods=["GET"])
def swagger_ui():
    """Serve Swagger UI with the API documentation"""
    return render_template("swagger.html")


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
