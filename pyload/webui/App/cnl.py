# -*- coding: utf-8 -*-

from __future__ import with_statement

import base64
import binascii
import os
import re
import urllib

import Crypto
import bottle

from pyload.webui import PYLOAD, DL_ROOT, JS


def local_check(function):

    def _view(*args, **kwargs):
        if bottle.request.environ.get("REMOTE_ADDR", "0") in ("127.0.0.1", "localhost") \
           or bottle.request.environ.get("HTTP_HOST", "0") in ("127.0.0.1:9666", "localhost:9666"):
            return function(*args, **kwargs)
        else:
            return bottle.HTTPError(403, "Forbidden")

    return _view


@bottle.route('/flash')
@bottle.route('/flash/<id>')
@bottle.route('/flash', method='POST')
@local_check
def flash(id="0"):
    return "JDownloader\r\n"


@bottle.route('/flash/add', method='POST')
@local_check
def add(request):
    package = bottle.request.POST.get('referer', None)
    urls = filter(lambda x: x != "", bottle.request.POST['urls'].split("\n"))

    if package:
        PYLOAD.addPackage(package, urls, 0)
    else:
        PYLOAD.generateAndAddPackages(urls, 0)

    return ""


@bottle.route('/flash/addcrypted', method='POST')
@local_check
def addcrypted():
    package = bottle.request.forms.get('referer', 'ClickNLoad Package')
    dlc = bottle.request.forms['crypted'].replace(" ", "+")

    dlc_path = os.path.join(DL_ROOT, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc")
    with open(dlc_path, "wb") as dlc_file:
        dlc_file.write(dlc)

    try:
        PYLOAD.addPackage(package, [dlc_path], 0)
    except Exception:
        return bottle.HTTPError()
    else:
        return "success\r\n"


@bottle.route('/flash/addcrypted2', method='POST')
@local_check
def addcrypted2():
    package = bottle.request.forms.get("source", None)
    crypted = bottle.request.forms['crypted']
    jk = bottle.request.forms['jk']

    crypted = base64.standard_b64decode(urllib.unquote(crypted.replace(" ", "+")))
    if JS:
        jk = "%s f()" % jk
        jk = JS.eval(jk)

    else:
        try:
            jk = re.findall(r"return ('|\")(.+)('|\")", jk)[0][1]
        except Exception:
            # Test for some known js functions to decode
            if jk.find("dec") > -1 and jk.find("org") > -1:
                org = re.findall(r"var org = ('|\")([^\"']+)", jk)[0][1]
                jk = list(org)
                jk.reverse()
                jk = "".join(jk)
            else:
                print "Could not decrypt key, please install py-spidermonkey or ossp-js"

    try:
        Key = binascii.unhexlify(jk)
    except Exception:
        print "Could not decrypt key, please install py-spidermonkey or ossp-js"
        return "failed"

    IV = Key

    obj = Crypto.Cipher.AES.new(Key, Crypto.Cipher.AES.MODE_CBC, IV)
    result = obj.decrypt(crypted).replace("\x00", "").replace("\r", "").split("\n")

    result = filter(lambda x: x != "", result)

    try:
        if package:
            PYLOAD.addPackage(package, result, 0)
        else:
            PYLOAD.generateAndAddPackages(result, 0)
    except Exception:
        return "failed can't add"
    else:
        return "success\r\n"


@bottle.route('/flashgot_pyload')
@bottle.route('/flashgot_pyload', method='POST')
@bottle.route('/flashgot')
@bottle.route('/flashgot', method='POST')
@local_check
def flashgot():
    if bottle.request.environ['HTTP_REFERER'] not in ("http://localhost:9666/flashgot", "http://127.0.0.1:9666/flashgot"):
        return bottle.HTTPError()

    autostart = int(bottle.request.forms.get('autostart', 0))
    package = bottle.request.forms.get('package', None)
    urls = filter(lambda x: x != "", bottle.request.forms['urls'].split("\n"))
    folder = bottle.request.forms.get('dir', None)

    if package:
        PYLOAD.addPackage(package, urls, autostart)
    else:
        PYLOAD.generateAndAddPackages(urls, autostart)

    return ""


@bottle.route('/crossdomain.xml')
@local_check
def crossdomain():
    rep = "<?xml version=\"1.0\"?>\n"
    rep += "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd\">\n"
    rep += "<cross-domain-policy>\n"
    rep += "<allow-access-from domain=\"*\" />\n"
    rep += "</cross-domain-policy>"
    return rep


@bottle.route('/flash/checkSupportForUrl')
@local_check
def checksupport():
    url = bottle.request.GET.get("url")
    res = PYLOAD.checkURLs([url])
    supported = (not res[0][1] is None)

    return str(supported).lower()


@bottle.route('/jdcheck.js')
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep
