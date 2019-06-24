#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os.path import join
import re
from urllib import unquote
from base64 import standard_b64decode
from binascii import unhexlify

from bottle import route, request, HTTPError
from webinterface import PYLOAD, DL_ROOT, JS

try:
    from Crypto.Cipher import AES
except:
    pass


def local_check(function):
    def _view(*args, **kwargs):
        if request.environ.get('REMOTE_ADDR', "0") in ('127.0.0.1', 'localhost') \
        or request.environ.get('HTTP_HOST','0') == '127.0.0.1:9666':
            return function(*args, **kwargs)
        else:
            return HTTPError(403, "Forbidden")

    return _view


@route("/flash")
@route("/flash/:id")
@route("/flash", method="POST")
@local_check
def flash(id="0"):
    return "JDownloader\r\n"

@route("/flash/add", method="POST")
@local_check
def add():
    package = request.forms.get("package", request.forms.get("source", request.POST.get('referer', None)))
    urls = [x.strip() for x in request.POST['urls'].split("\n") if x.strip()]

    if package:
        PYLOAD.addPackage(package, urls, 0)
    else:
        PYLOAD.generateAndAddPackages(urls, 0)

    return ""

@route("/flash/addcrypted", method="POST")
@local_check
def addcrypted():
    package = request.forms.get("package", request.forms.get("source", request.POST.get('referer', None)))
    dlc = request.forms['crypted'].replace(" ", "+")

    dlc_path = join(DL_ROOT, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc")
    dlc_file = open(dlc_path, "wb")
    dlc_file.write(dlc)
    dlc_file.close()

    try:
        PYLOAD.addPackage(package, [dlc_path], 0)
    except:
        return HTTPError()
    else:
        return "success\r\n"

@route("/flash/addcrypted2", method="POST")
@local_check
def addcrypted2():
    package = request.forms.get("package", request.forms.get("source", request.POST.get('referer', None)))
    crypted = request.forms["crypted"]
    jk = request.forms["jk"]

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    if JS:
        jk = "%s f()" % jk
        jk = JS.eval(jk)

    else:
        try:
            jk = re.findall(r"return ('|\")(.+)('|\")", jk)[0][1]
        except:
        ## Test for some known js functions to decode
            if jk.find("dec") > -1 and jk.find("org") > -1:
                org = re.findall(r"var org = ('|\")([^\"']+)", jk)[0][1]
                jk = list(org)
                jk.reverse()
                jk = "".join(jk)
            else:
                print "Could not decrypt key, please install py-spidermonkey or ossp-js"

    try:
        Key = unhexlify(jk)
    except:
        print "Could not decrypt key, please install py-spidermonkey or ossp-js"
        return "failed"

    IV = Key

    obj = AES.new(Key, AES.MODE_CBC, IV)
    urls = obj.decrypt(crypted).replace("\x00", "").replace("\r","").split("\n")

    urls = [x.strip() for x in urls if x.strip()]

    try:
        if package:
            PYLOAD.addPackage(package, urls, 0)
        else:
            PYLOAD.generateAndAddPackages(urls, 0)
    except:
        return "failed can't add"
    else:
        return "success\r\n"

@route("/flashgot_pyload")
@route("/flashgot_pyload", method="POST")
@route("/flashgot")
@route("/flashgot", method="POST")
@local_check
def flashgot():
    if request.environ['HTTP_REFERER'] != "http://localhost:9666/flashgot" and request.environ['HTTP_REFERER'] != "http://127.0.0.1:9666/flashgot":
        return HTTPError()

    autostart = int(request.forms.get('autostart', 0))
    package = request.forms.get('package', None)
    urls = [x.strip() for x in request.POST['urls'].split("\n") if x.strip()]
    folder = request.forms.get('dir', None)

    if package:
        PYLOAD.addPackage(package, urls, autostart)
    else:
        PYLOAD.generateAndAddPackages(urls, autostart)

    return ""

@route("/crossdomain.xml")
@local_check
def crossdomain():
    rep = "<?xml version=\"1.0\"?>\n"
    rep += "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd\">\n"
    rep += "<cross-domain-policy>\n"
    rep += "<allow-access-from domain=\"*\" />\n"
    rep += "</cross-domain-policy>"
    return rep


@route("/flash/checkSupportForUrl")
@local_check
def checksupport():
    url = request.GET.get("url")
    res = PYLOAD.checkURLs([url])
    supported = (not res[0][1] is None)

    return str(supported).lower()

@route("/jdcheck.js")
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep
