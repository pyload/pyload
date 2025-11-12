# -*- coding: utf-8 -*-
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
from ..helpers import apikey_auth, clear_session, is_authenticated, render_template, set_session

bp = flask.Blueprint("api", __name__)
log = getLogger(APPID)


# accepting positional arguments, as well as kwargs via post and get
@bp.route("/api/<func>", methods=["GET", "POST"], endpoint="rpc")
@bp.route("/api/<func>/<args>", methods=["GET", "POST"], endpoint="rpc")
# @apiver_check
@apikey_auth
def rpc(func, args=""):
    api = flask.current_app.config["PYLOAD_API"]

    # Get user info from API auth or session
    if hasattr(flask.g, 'user_info'):
        # Using API auth
        user_info = flask.g.user_info
    else:
        # Using session auth
        s = flask.session
        if not is_authenticated(s):
            return jsonify({'error': "Unauthorized - Login required"}), 401
        user_info = {"role": s["role"], "permission": s["perms"]}

    # Check permissions
    if not api.is_authorized(func, {"role": user_info["role"], "permission": user_info["permission"]}):
        log.error(f"API access denied for function '{func}'")
        return jsonify({'error': "Unauthorized - Insufficient permissions"}), 401

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


@bp.route("/api", methods=["GET"], strict_slashes=False)
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

    client_ip = flask.request.headers.get("X-Forwarded-For", "").split(',')[0].strip() or flask.request.remote_addr

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
