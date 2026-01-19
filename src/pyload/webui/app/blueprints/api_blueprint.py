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
from ..helpers import apikey_auth, csrf_exempt, is_authenticated, render_template

bp = flask.Blueprint("api", __name__)
log = getLogger(APPID)


# accepting positional arguments, as well as kwargs via post and get
@bp.route("/api/<func>", methods=["GET", "POST"], endpoint="rpc")
@bp.route("/api/<func>/<args>", methods=["GET", "POST"], endpoint="rpc")
# @apiver_check
@apikey_auth
def rpc(func, args=""):
    if func.startswith("_"):
        flask.flash(f"Invalid API call '{func}'")
        return jsonify({'error': "Forbidden"}), 403

    api = flask.current_app.config["PYLOAD_API"]

    # Enforce HTTP method for the API method
    expected = api._required_http_method_for_api(func)
    actual = flask.request.method
    if actual != expected:
        err_message = f"Method not allowed in API {func}(): Expected {expected}, got {actual}"
        log.error(err_message)
        return jsonify({'error': err_message}), 405

    # Get user info from API auth or session
    if not hasattr(flask.g, 'user_info'):
        return jsonify({'error': "Unauthorized - Login required"}), 401

    # Check permissions
    user_info = flask.g.user_info
    if not api.is_authorized(func, {"role": user_info["role"], "permission": user_info["permission"]}):
        log.error(f"API access denied for function '{func}'")
        return jsonify({'error': "Unauthorized - Insufficient permissions"}), 401

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
        except (ValueError, SyntaxError):
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
    return flask.send_from_directory("static", "swagger.html")


@bp.route("/api/login", methods=["POST"], endpoint="login")
@csrf_exempt
# @apiver_check
def login():
    return "Obsolete API", 404


@bp.route("/api/logout", endpoint="logout")
# @apiver_check
def logout():
    return "Obsolete API", 404
