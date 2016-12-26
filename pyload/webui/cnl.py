# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import str
from os.path import join
import re
from urllib.parse import unquote
from base64 import standard_b64decode
from binascii import unhexlify
from traceback import print_exc

from pyload.utils.fs import safe_filename

from bottle import route, request, HTTPError
from pyload.webui.webinterface import PYLOAD, DL_ROOT, JS

try:
    from Crypto.Cipher import AES
except Exception:
    pass

def generate_and_add(urls, paused):
    packs = PYLOAD.generate_packages(urls)
    for name, urls in packs.items():
        PYLOAD.add_package(name, urls, paused=paused)

def local_check(function):
    def _view(*args, **kwargs):
        if request.environ.get('REMOTE_ADDR', "0") in ('127.0.0.1', 'localhost') \
        or request.environ.get('HTTP_HOST', '0') in ('127.0.0.1:9666', 'localhost:9666'):
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
def add(request):
    package = request.POST.get('referer', None)
    urls = [x for x in request.POST['urls'].split("\n") if x != ""]

    if package:
        PYLOAD.add_package(package, urls, paused=True)
    else:
        generate_and_add(urls, True)

    return ""

@route("/flash/addcrypted", method="POST")
@local_check
def addcrypted():

    package = request.forms.get('referer', 'ClickAndLoad Package')
    dlc = request.forms['crypted'].replace(" ", "+")

    dlc_path = join(DL_ROOT, safe_filename(package) + ".dlc")
    dlc_file = open(dlc_path, "wb")
    dlc_file.write(dlc)
    dlc_file.close()

    try:
        PYLOAD.add_package(package, [dlc_path], paused=True)
    except Exception:
        return HTTPError()
    else:
        return "success\r\n"

@route("/flash/addcrypted2", method="POST")
@local_check
def addcrypted2():

    package = request.forms.get("source", None)
    crypted = request.forms["crypted"]
    jk = request.forms["jk"]

    crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
    if JS:
        jk = "%s f()" % jk
        jk = JS.eval(jk)

    else:
        try:
            jk = re.findall(r"return ('|\")(.+)('|\")", jk)[0][1]
        except Exception:
        ## Test for some known js functions to decode
            if jk.find("dec") > -1 and jk.find("org") > -1:
                org = re.findall(r"var org = ('|\")([^\"']+)", jk)[0][1]
                jk = reversed(org)
                jk = "".join(jk)
            else:
                print("Could not decrypt key, please install py-spidermonkey or ossp-js")

    try:
        Key = unhexlify(jk)
    except Exception:
        print("Could not decrypt key, please install py-spidermonkey or ossp-js")
        return "failed"

    IV = Key

    obj = AES.new(Key, AES.MODE_CBC, IV)
    result = obj.decrypt(crypted).replace("\x00", "").replace("\r", "").split("\n")

    result = [x for x in result if x != ""]

    try:
        if package:
            PYLOAD.add_package(package, result, paused=True)
        else:
            generate_and_add(result, True)
    except Exception:
        print_exc()
        return "failed"
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

    autostart = bool(int(request.forms.get('autostart', 0)))
    package = request.forms.get('package', None)
    urls = [x for x in request.forms['urls'].split("\n") if x != ""]

    # TODO: folder?
    folder = request.forms.get('dir', None)

    if package:
        PYLOAD.add_package(package, urls, paused=autostart)
    else:
        generate_and_add(urls, autostart)
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
    res = PYLOAD.check_urls([url])
    supported = (not res[0][1] is None)

    return str(supported).lower()

@route("/jdcheck.js")
@local_check
def jdcheck():
    rep = "jdownloader=true;\n"
    rep += "var version='9.581;'"
    return rep
