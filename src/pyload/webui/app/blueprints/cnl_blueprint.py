# -*- coding: utf-8 -*-

import os
from base64 import standard_b64decode
from functools import wraps
from urllib.parse import unquote

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import flask
from flask.json import jsonify
from pyload.core.api import Destination
from pyload.core.utils.convert import to_str
from pyload.core.utils.misc import eval_js

#: url_prefix here is intentional since it should not be affected by path prefix
bp = flask.Blueprint("flash", __name__, url_prefix="/")


#: decorator
def local_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        remote_addr = flask.request.environ.get("REMOTE_ADDR", "0")
        http_host = flask.request.environ.get("HTTP_HOST", "0")

        if remote_addr in ("127.0.0.1", "::ffff:127.0.0.1", "::1", "localhost") or http_host in (
            "127.0.0.1:9666",
            "[::1]:9666",
        ):
            return func(*args, **kwargs)
        else:
            return "Forbidden", 403

    return wrapper


@bp.after_request
def add_cors(response):
    response.headers.update({
        'Access-Control-Max-Age': 1800,
        'Access-Control-Allow-Origin': "*",
        'Access-Control-Allow-Methods': "OPTIONS, GET, POST"
    })
    return response


@bp.route("/flash/", methods=["GET", "POST"], endpoint="index")
@bp.route("/flash/<id>", methods=["GET", "POST"], endpoint="index")
@local_check
def index(id="0"):
    return "JDownloader\r\n"


@bp.route("/flash/add", methods=["POST"], endpoint="add")
@local_check
def add():
    package = flask.request.form.get(
        "package", flask.request.form.get("source", flask.request.form.get("referer"))
    )

    urls = [url.strip() for url in unquote(flask.request.form["urls"]).replace(' ', '\n').split("\n") if url.strip()]
    if not urls:
        return "failed no urls\r\n", 500

    pack_password = flask.request.form.get("passwords")

    api = flask.current_app.config["PYLOAD_API"]
    try:
        if package:
            pack = api.add_package(package, urls, Destination.COLLECTOR)
        else:
            pack = api.generate_and_add_packages(urls, Destination.COLLECTOR)
    except Exception as exc:
        return "failed " + str(exc) + "\r\n", 500

    if pack_password:
        api.set_package_data(pack, {"password": pack_password})

    return "success\r\n"


@bp.route("/flash/addcrypted", methods=["POST"], endpoint="addcrypted")
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

    pack_password = flask.request.form.get("passwords")

    try:
        pack = api.add_package(package, [dlc_path], Destination.COLLECTOR)
    except Exception as exc:
        return "failed " + str(exc) + "\r\n", 500
    else:
        if pack_password:
            api.set_package_data(pack, {"password": pack_password})

        return "success\r\n"


@bp.route("/flash/addcrypted2", methods=["POST"], endpoint="addcrypted2")
@local_check
def addcrypted2():
    package = flask.request.form.get(
        "package", flask.request.form.get("source", flask.request.form.get("referer"))
    )
    crypted = flask.request.form["crypted"]
    jk = flask.request.form["jk"]
    pack_password = flask.request.form.get("passwords")

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    jk = eval_js(f"{jk} f()")

    try:
        IV = key = bytes.fromhex(jk)
    except Exception:
        return "Could not decrypt key", 500

    cipher = Cipher(
        algorithms.AES(key), modes.CBC(IV), backend=default_backend()
    )
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(crypted) + decryptor.finalize()
    urls = to_str(decrypted).replace("\x00", "").replace("\r", "").split("\n")
    urls = [url for url in urls if url.strip()]

    api = flask.current_app.config["PYLOAD_API"]
    try:
        if package:
            pack = api.add_package(package, urls, Destination.COLLECTOR)
        else:
            pack = api.generate_and_add_packages(urls, Destination.COLLECTOR)
    except Exception as exc:
        return "failed " + str(exc) + "\r\n", 500
    else:
        if pack_password:
            api.set_package_data(pack, {"password": pack_password})

        return "success\r\n"


@bp.route("/flashgot", methods=["POST"], endpoint="flashgot")
@bp.route("/flashgot_pyload", methods=["POST"], endpoint="flashgot")
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
        api.add_package(package, urls, Destination.QUEUE if autostart else Destination.COLLECTOR)
    else:
        api.generate_and_add_packages(urls, Destination.QUEUE if autostart else Destination.COLLECTOR)


@bp.route("/crossdomain.xml", endpoint="crossdomain")
@local_check
def crossdomain():
    rep = '<?xml version="1.0"?>\n'
    rep += '<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n'
    rep += "<cross-domain-policy>\n"
    rep += '<allow-access-from domain="*" />\n'
    rep += "</cross-domain-policy>"
    return rep


@bp.route("/flash/checkSupportForUrl", methods=["POST"], endpoint="checksupport")
@local_check
def checksupport():
    api = flask.current_app.config["PYLOAD_API"]

    url = flask.request.form["url"]
    res = api.check_urls([url])

    supported = not res[0][1] is None
    return str(supported).lower()


@bp.route("/jdcheck.js", endpoint="jdcheck")
@local_check
def jdcheck():
    rep = "jdownloader=true;\r\n"
    rep += "var version='42707';\r\n"
    return rep
