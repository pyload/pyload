# Create your views here.


from django.conf import settings
from django.http import HttpResponse
from django.http import HttpResponseServerError
from os.path import join
import binascii
from urllib import unquote
import re
import base64

try:
    from Crypto.Cipher import AES
except:
    pass

def flash(request):
    return HttpResponse()

def add(request):
    package = request.POST.get('referer','ClickAndLoad Package')
    urls = filter(lambda x: x != "", request.POST['urls'].split("\n"))
    
    settings.PYLOAD.add_package(package, urls, False)
    
    return HttpResponse()

def addcrypted(request):
    
    package = request.POST.get('referer','ClickAndLoad Package')
    dlc = request.POST['crypted'].replace(" ","+")
    
    dlc_path = join(settings.DL_ROOT, package.replace("/","").replace("\\","").replace(":","")+".dlc")
    dlc_file = file(dlc_path, "wb")
    dlc_file.write(dlc)
    dlc_file.close()
    
    
    settings.PYLOAD.add_package(package, [dlc_path], False)
    
    return HttpResponse()

def addcrypted2(request):

    package = request.POST.get("source", "ClickAndLoad Package")
    crypted = request.POST["crypted"]
    jk = request.POST["jk"]
    
    crypted = base64.standard_b64decode(unquote(crypted.replace(" ","+")))
    
    jk = re.findall(r"return ('|\")(.+)('|\")", jk)[0][1]
    
    Key = binascii.unhexlify(jk)
    IV = Key
    
    obj = AES.new(Key, AES.MODE_CBC, IV)
    result = obj.decrypt(crypted).replace("\x00","").split("\n")
    
    settings.PYLOAD.add_package(package, result, False)
    
    return HttpResponse()

def flashgot(request):
    if request.META['HTTP_REFERER'] != "http://localhost:9666/flashgot" and request.META['HTTP_REFERER'] != "http://127.0.0.1:9666/flashgot":
        return HttpResponseServerError()
    
    autostart = int(request.POST.get('autostart',0))
    package = request.POST.get('package', "FlashGot")
    urls = request.POST['urls'].split("\n")
    folder = request.POST.get('dir', None)

    settings.PYLOAD.add_package(package, urls, autostart)
    
    return HttpResponse("")

def crossdomain(request):
    rep = "<?xml version=\"1.0\"?>\r\n"
    rep += "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd\">\r\n"
    rep += "<cross-domain-policy>\r\n"
    rep += "<allow-access-from domain=\"*\" />\r\n"
    rep += "</cross-domain-policy>\r\n"
    return HttpResponse(rep)