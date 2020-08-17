# -*- coding: utf-8 -*-

import os
from base64 import standard_b64decode
from functools import wraps
from urllib.parse import unquote

import flask
from cryptography.fernet import Fernet
from flask.json import jsonify

from pyload.core.utils.misc import eval_js

from .app_blueprint import bp as app_bp

bp = flask.Blueprint("flash", __name__, url_prefix="/flash")


#: decorator
def local_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        remote_addr = flask.request.environ.get("REMOTE_ADDR", "0")
        http_host = flask.request.environ.get("HTTP_HOST", "0")

        if remote_addr in ("127.0.0.1", "localhost") or http_host in (
            "127.0.0.1:9666",
            "localhost:9666",
        ):
            return func(*args, **kwargs)
        else:
            return "Forbidden", 403

    return wrapper


@bp.route("/", methods=["GET", "POST"], endpoint="index")
@bp.route("/<id>", methods=["GET", "POST"], endpoint="index")
@local_check
def index(id="0"):
    return "JDownloader\r\n"


@bp.route("/add", methods=["POST"], endpoint="add")
@local_check
def add():
    package = flask.request.form.get(
        "package", flask.request.form.get("source", flask.request.form.get("referer"))
    )

    urls = [url for url in flask.request.form["urls"].split("\n") if url.strip()]
    if not urls:
        return jsonify(False)

    api = flask.current_app.config["PYLOAD_API"]
    if package:
        api.add_package(package, urls, 0)
    else:
        api.generate_and_add_packages(urls, 0)


@bp.route("/addcrypted", methods=["POST"], endpoint="addcrypted")
@local_check
def addcrypted():
    api = flask.current_app.config["PYLOAD_API"]

    package = flask.request.form.get(
        "package", flask.request.form.get("source", flask.request.form.get("referer"))
    )
    dl_path = api.get_config_value("general", "storage_folder")
    dlc_path = os.path.join(
        dl_path, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc"
    )
    dlc = flask.request.form["crypted"].replace(" ", "+")
    with open(dlc_path, mode="wb") as fp:
        fp.write(dlc)

    try:
        api.add_package(package, [dlc_path], 0)
    except Exception:
        flask.abort(500)
    else:
        return "success\r\n"


@bp.route("/addcrypted2", methods=["POST"], endpoint="addcrypted2")
@local_check
def addcrypted2():
    package = flask.request.form.get(
        "package", flask.request.form.get("source", flask.request.form.get("referer"))
    )
    crypted = flask.request.form["crypted"]
    jk = flask.request.form["jk"]

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    jk = eval_js(f"{jk} f()")

    try:
        key = bytes.fromhex(jk)
    except Exception:
        return "Could not decrypt key", 500

    obj = Fernet(key)
    urls = obj.decrypt(crypted).replace("\x00", "").replace("\r", "").split("\n")
    urls = [url for url in urls if url.strip()]

    api = flask.current_app.config["PYLOAD_API"]
    try:
        if package:
            api.add_package(package, urls, 0)
        else:
            api.generate_and_add_packages(urls, 0)
    except Exception:
        return "failed can't add", 500
    else:
        return "success\r\n"


@app_bp.route("/flashgot", methods=["POST"], endpoint="flashgot")
@app_bp.route("/flashgot_pyload", methods=["POST"], endpoint="flashgot")
@local_check
def flashgot():
    if flask.request.referrer not in (
        "http://localhost:9666/flashgot",
        "http://127.0.0.1:9666/flashgot",
    ):
        flask.abort(500)

    package = flask.request.form.get("package")
    urls = [url for url in flask.request.form["urls"].split("\n") if url.strip()]
    # folder = flask.request.form.get('dir', None)
    autostart = int(flask.request.form.get("autostart", 0))

    api = flask.current_app.config["PYLOAD_API"]
    if package:
        api.add_package(package, urls, autostart)
    else:
        api.generate_and_add_packages(urls, autostart)


@app_bp.route("/crossdomain.xml", endpoint="crossdomain")
@local_check
def crossdomain():
    rep = '<?xml version="1.0"?>\n'
    rep += '<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n'
    rep += "<cross-domain-policy>\n"
    rep += '<allow-access-from domain="*" />\n'
    rep += "</cross-domain-policy>"
    return rep


@bp.route("/check_support_for_url", methods=["POST"], endpoint="checksupport")
@local_check
def checksupport():
    api = flask.current_app.config["PYLOAD_API"]

    url = flask.request.form["url"]
    res = api.check_urls([url])

    supported = not res[0][1] is None
    return str(supported).lower()


@app_bp.route("/jdcheck.js", endpoint="jdcheck")
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep
