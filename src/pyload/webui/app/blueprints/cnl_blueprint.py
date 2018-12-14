# -*- coding: utf-8 -*-


import os
from base64 import standard_b64decode
from builtins import str
from functools import wraps
from urllib.parse import unquote

import flask
import js2py
from cryptography.fernet import Fernet
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
@bp.route("/<id>", endpoint="index")
@local_check
def flash(id="0"):
    return "JDownloader\r\n"


@bp.route("/add", methods=["POST"], endpoint="add")
@local_check
def add():
    package = flask.request.form.get(
        "package",
        flask.request.form.get("source", flask.request.form.get("referer", None)),
    )
    
    urls = flask.request.form.get("urls")
    if not urls:
        return jsonify(False)
    
    urls = list(filter(None, map(str.strip, urls.split("\n"))))

    api = flask.current_app.config["PYLOAD_API"]
    if package:
        api.addPackage(package, urls, 0)
    else:
        api.generateAndAddPackages(urls, 0)


@bp.route("/addcrypted", methods=["POST"], endpoint="addcrypted")
@local_check
def addcrypted():
    package = flask.request.form.get(
        "package",
        flask.request.form.get("source", flask.request.form.get("referer", None)),
    )
    dlc = flask.request.form["crypted"].replace(" ", "+")

    api = flask.current_app.config["PYLOAD_API"]

    dl_path = api.getConfigValue("general", "storage_folder")
    dlc_path = os.path.join(
        dl_path, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc"
    )
    with open(dlc_path, mode="wb") as dlc_file:
        dlc_file.write(dlc)

    try:
        api.addPackage(package, [dlc_path], 0)
    except Exception:
        flask.abort(500)
    else:
        return "success\r\n"


@bp.route("/addcrypted2", methods=["POST"], endpoint="addcrypted2")
@local_check
def addcrypted2():
    package = flask.request.form.get(
        "package",
        flask.request.form.get("source", flask.request.form.get("referer", None)),
    )
    crypted = flask.request.form["crypted"]
    jk = flask.request.form["jk"]

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    jk = js2py.eval_js("{jk} f()")

    try:
        key = bytes.fromhex(jk)
    except Exception:
        return "Could not decrypt key", 500

    obj = Fernet(key)
    urls = obj.decrypt(crypted).replace("\x00", "").replace("\r", "").split("\n")

    urls = list(filter(None, map(str.strip, urls)))

    api = flask.current_app.config["PYLOAD_API"]
    try:
        if package:
            api.addPackage(package, urls, 0)
        else:
            api.generateAndAddPackages(urls, 0)
    except Exception:
        return "failed can't add", 500
    else:
        return "success\r\n"


@app_bp.route("/flashgot", methods=["GET", "POST"], endpoint="flashgot")
@app_bp.route("/flashgot_pyload", methods=["GET", "POST"], endpoint="flashgot")
@local_check
def flashgot():
    if flask.request.referrer not in (
        "http://localhost:9666/flashgot",
        "http://127.0.0.1:9666/flashgot",
    ):
        flask.abort(500)

    autostart = int(flask.request.form.get("autostart", 0))
    package = flask.request.form.get("package", None)

    urls = list(filter(None, map(str.strip, flask.request.form["urls"].split("\n"))))
    # folder = flask.request.form.get('dir', None)

    api = flask.current_app.config["PYLOAD_API"]
    if package:
        api.addPackage(package, urls, autostart)
    else:
        api.generateAndAddPackages(urls, autostart)


@app_bp.route("/crossdomain.xml", endpoint="crossdomain")
@local_check
def crossdomain():
    rep = '<?xml version="1.0"?>\n'
    rep += '<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n'
    rep += "<cross-domain-policy>\n"
    rep += '<allow-access-from domain="*" />\n'
    rep += "</cross-domain-policy>"
    return rep


@bp.route("/checkSupportForUrl", endpoint="checksupport")
@local_check
def checksupport():
    api = flask.current_app.config["PYLOAD_API"]
    url = flask.request.form.get("url")
    res = api.checkURLs([url])
    supported = not res[0][1] is None

    return str(supported).lower()


@app_bp.route("/jdcheck.js", endpoint="jdcheck")
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep
