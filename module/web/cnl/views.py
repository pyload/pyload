# Create your views here.


import base64
import binascii
from os.path import join
import re
from urllib import unquote

from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseServerError

try:
    from Crypto.Cipher import AES
except:
    pass

def local_check(function):
    def _dec(view_func):
        def _view(request, * args, ** kwargs):
            if request.META['REMOTE_ADDR'] == '127.0.0.1' or request.META['REMOTE_ADDR'] == 'localhost':
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

@local_check
def flash(request):
    return HttpResponse()

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
    
    
    settings.PYLOAD.add_package(package, [dlc_path], False)
    
    return HttpResponse()

@local_check
def addcrypted2(request):

    package = request.POST.get("source", "ClickAndLoad Package")
    crypted = request.POST["crypted"]
    jk = request.POST["jk"]
    
    crypted = base64.standard_b64decode(unquote(crypted.replace(" ", "+")))
    
    jk = re.findall(r"return ('|\")(.+)('|\")", jk)[0][1]
    
    Key = binascii.unhexlify(jk)
    IV = Key
    
    obj = AES.new(Key, AES.MODE_CBC, IV)
    result = obj.decrypt(crypted).replace("\x00", "").split("\n")

    result = filter(lambda x: x != "", result)

    settings.PYLOAD.add_package(package, result, False)
    
    return HttpResponse()

@local_check
def flashgot(request):
    if request.META['HTTP_REFERER'] != "http://localhost:9666/flashgot" and request.META['HTTP_REFERER'] != "http://127.0.0.1:9666/flashgot":
        return HttpResponseServerError()
    
    autostart = int(request.POST.get('autostart', 0))
    package = request.POST.get('package', "FlashGot")
    urls = urls = filter(lambda x: x != "", request.POST['urls'].split("\n"))
    folder = request.POST.get('dir', None)

    settings.PYLOAD.add_package(package, urls, autostart)
    
    return HttpResponse("")

@local_check
def crossdomain(request):
    rep = "<?xml version=\"1.0\"?>\r\n"
    rep += "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd\">\r\n"
    rep += "<cross-domain-policy>\r\n"
    rep += "<allow-access-from domain=\"*\" />\r\n"
    rep += "</cross-domain-policy>\r\n"
    return HttpResponse(rep)