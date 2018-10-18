# -*- coding: utf-8 -*-

from pyload.webui.app import app

import json
import os
import re
from base64 import standard_b64decode
from binascii import unhexlify
from builtins import str
from urllib.parse import unquote

import flask
import js2py
from cryptography.fernet import Fernet

from pyload.webui.server_thread import PYLOAD_API


def local_check(func):
    def _view(*args, **kwargs):
        if bottle.request.environ.get("REMOTE_ADDR", "0") in (
            "127.0.0.1",
            "localhost",
        ) or bottle.request.environ.get("HTTP_HOST", "0") in (
            "127.0.0.1:9666",
            "localhost:9666",
        ):
            return func(*args, **kwargs)
        else:
            return bottle.HTTPError(403, json.dumps("Forbidden"))

    return _view


@app.route(r"/flash/<id>")
@app.route(r"/flash", methods=['GET', 'POST'])
@local_check
def flash(id="0"):
    return "JDownloader\r\n"


@app.route(r"/flash/add", methods=['POST'])
@local_check
def add():
    package = bottle.request.forms.get(
        "package",
        bottle.request.forms.get("source", bottle.request.POST.get("referer", None)),
    )
    urls = list(filter(None, map(str.strip, bottle.request.POST["urls"].split("\n"))))

    if package:
        PYLOAD_API.addPackage(package, urls, 0)
    else:
        PYLOAD_API.generateAndAddPackages(urls, 0)

    return ""


@app.route(r"/flash/addcrypted", methods=['POST'])
@local_check
def addcrypted():
    package = bottle.request.forms.get(
        "package",
        bottle.request.forms.get("source", bottle.request.POST.get("referer", None)),
    )
    dlc = bottle.request.forms["crypted"].replace(" ", "+")

    dl_path = PYLOAD_API.getConfigValue("general", "download_folder")
    dlc_path = os.path.join(
        dl_path, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc"
    )
    with open(dlc_path, mode="wb") as dlc_file:
        dlc_file.write(dlc)

    try:
        PYLOAD_API.addPackage(package, [dlc_path], 0)
    except Exception:
        return bottle.HTTPError()
    else:
        return "success\r\n"


@app.route(r"/flash/addcrypted2", methods=['POST'])
@local_check
def addcrypted2():
    package = bottle.request.forms.get(
        "package",
        bottle.request.forms.get("source", bottle.request.POST.get("referer", None)),
    )
    crypted = bottle.request.forms["crypted"]
    jk = bottle.request.forms["jk"]

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    jk = "{} f()".format(jk)
    jk = js2py.eval_js(jk)

    try:
        key = unhexlify(jk)
    except Exception:
        print("Could not decrypt key, please install py-spidermonkey or ossp-js")
        return "failed"

    obj = Fernet(key)
    urls = obj.decrypt(crypted).replace("\x00", "").replace("\r", "").split("\n")

    urls = list(filter(None, map(str.strip, urls)))

    try:
        if package:
            PYLOAD_API.addPackage(package, urls, 0)
        else:
            PYLOAD_API.generateAndAddPackages(urls, 0)
    except Exception:
        return "failed can't add"
    else:
        return "success\r\n"


@app.route(r"/flashgot_pyload", methods=['GET', 'POST'])
@app.route(r"/flashgot", methods=['GET', 'POST'])
@local_check
def flashgot():
    if bottle.request.environ["HTTP_REFERER"] not in (
        "http://localhost:9666/flashgot",
        "http://127.0.0.1:9666/flashgot",
    ):
        return bottle.HTTPError()

    autostart = int(bottle.request.forms.get("autostart", 0))
    package = bottle.request.forms.get("package", None)

    urls = list(filter(None, map(str.strip, bottle.request.POST["urls"].split("\n"))))
    # folder = bottle.request.forms.get('dir', None)

    if package:
        PYLOAD_API.addPackage(package, urls, autostart)
    else:
        PYLOAD_API.generateAndAddPackages(urls, autostart)

    return ""


@app.route(r"/crossdomain.xml")
@local_check
def crossdomain():
    rep = '<?xml version="1.0"?>\n'
    rep += '<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">\n'
    rep += "<cross-domain-policy>\n"
    rep += '<allow-access-from domain="*" />\n'
    rep += "</cross-domain-policy>"
    return rep


@app.route(r"/flash/checkSupportForUrl")
@local_check
def checksupport():
    url = bottle.request.GET.get("url")
    res = PYLOAD_API.checkURLs([url])
    supported = not res[0][1] is None

    return str(supported).lower()


@app.route(r"/jdcheck.js")
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep
