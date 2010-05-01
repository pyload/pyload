# Create your views here.


import base64
import binascii
from os.path import join
import re
from urllib import unquote

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseServerError

from django.core.serializers import json
from django.utils import simplejson

try:
    from Crypto.Cipher import AES
except:
    pass

def local_check(function):
    def _dec(view_func):
        def _view(request, * args, ** kwargs):
            if request.META.get('REMOTE_ADDR', "0") in ('127.0.0.1','localhost') or request.META.get('HTTP_HOST','0') == '127.0.0.1:9666':
                return view_func(request, * args, ** kwargs)
            else:
                return HttpResponseServerError()

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)

class JsonResponse(HttpResponse):
    def __init__(self, obj, request):
        cb = request.GET.get("callback")
        if cb:
            obj = {"content": obj}
            content = simplejson.dumps(obj, indent=2, cls=json.DjangoJSONEncoder, ensure_ascii=False)
            content = "%s(%s)\r\n" % (cb, content)
            HttpResponse.__init__(self, content, content_type="application/json")
        else:
            content = "%s\r\n" % obj
            HttpResponse.__init__(self, content, content_type="text/html")
        self["Cache-Control"] = "no-cache, must-revalidate"

@local_check
def flash(request):
    return HttpResponse("JDownloader\r\n")

@local_check
def add(request):
    package = request.POST.get('referer', 'ClickAndLoad Package')
    urls = filter(lambda x: x != "", request.POST['urls'].split("\n"))
    
    settings.PYLOAD.add_package(package, urls, False)
    
    return HttpResponse()

@local_check
def addcrypted(request):
    
    package = request.POST.get('referer', 'ClickAndLoad Package')
    dlc = request.POST['crypted'].replace(" ", "+")
    
    dlc_path = join(settings.DL_ROOT, package.replace("/", "").replace("\\", "").replace(":", "") + ".dlc")
    dlc_file = file(dlc_path, "wb")
    dlc_file.write(dlc)
    dlc_file.close()
    
    try:
        settings.PYLOAD.add_package(package, [dlc_path], False)
    except:
        return JsonResponse("", request)
    else:
        return JsonResponse("success", request)

@local_check
def addcrypted2(request):

    package = request.POST.get("source", "ClickAndLoad Package")
    crypted = request.POST["crypted"]
    jk = request.POST["jk"]
    
    crypted = base64.standard_b64decode(unquote(crypted.replace(" ", "+")))
    
    try:
        import spidermonkey
    except:
        try:
            jk = re.findall(r"return ('|\")(.+)('|\")", jk)[0][1]
        except:
            ## Test for some known js functions to decode
            if jk.find("dec") > -1 and jk.find("org") > -1:
                org = re.findall(r"var org = ('|\")([^\"']+)", jk)[0][1]
                jk = list(org)
                jk.reverse()
                jk = "".join(jk)
                print jk
    else:
        rt = spidermonkey.Runtime()
        cx = rt.new_context()
        jk = cx.execute("%s f()" % jk)
        

    Key = binascii.unhexlify(jk)
    IV = Key
    
    obj = AES.new(Key, AES.MODE_CBC, IV)
    result = obj.decrypt(crypted).replace("\x00", "").replace("\r","").split("\n")

    result = filter(lambda x: x != "", result)

    try:
        settings.PYLOAD.add_package(package, result, False)
    except:
        return JsonResponse("failed can't add", request)
    else:
        return JsonResponse("success", request)

@local_check
def flashgot(request):
    if request.META['HTTP_REFERER'] != "http://localhost:9666/flashgot" and request.META['HTTP_REFERER'] != "http://127.0.0.1:9666/flashgot":
        return HttpResponseServerError()
    
    autostart = int(request.POST.get('autostart', 0))
    package = request.POST.get('package', "FlashGot")
    urls = urls = filter(lambda x: x != "", request.POST['urls'].split("\n"))
    folder = request.POST.get('dir', None)

    settings.PYLOAD.add_package(package, urls, autostart)
    
    return HttpResponse("\r\n")

@local_check
def crossdomain(request):
    rep = "<?xml version=\"1.0\"?>\n"
    rep += "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd\">\n"
    rep += "<cross-domain-policy>\n"
    rep += "<allow-access-from domain=\"*\" />\n"
    rep += "</cross-domain-policy>"
    return HttpResponse(rep)

@local_check
def jdcheck(request):
    rep = "jdownloader=true;\n"
    rep += "var version='10629';\n"
    return HttpResponse(rep)
