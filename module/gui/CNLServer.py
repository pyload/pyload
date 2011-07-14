# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""
import re
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from cgi import FieldStorage
from os.path import abspath, dirname, join
from urllib import unquote
from base64 import standard_b64decode
from binascii import unhexlify

try:
    from Crypto.Cipher import AES
except:
    pass

try:
    from module.common import JsEngine
except ImportError:
    import sys
    sys.path.append(join(abspath(dirname(__file__)), "..", ".."))
    from module.common import JsEngine

js = JsEngine.JsEngine()
core = None

class CNLServer(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.setDaemon(True)
        
        self.stop = False
        self.stopped = False

    def run(self):
        server_address = ('127.0.0.1', 9666)
        try:
            httpd = HTTPServer(server_address, CNLHandler)
        except:
            self.stopped = True
            return
        
        self.stopped = False
        while self.keep_running():
            httpd.handle_request()
        self.stopped = True

    def keep_running(self):
        return not self.stop


class CNLHandler(BaseHTTPRequestHandler):

    #def log_message(self, *args):
    #    pass

    def add_package(self, name, urls, queue=0):
        print "name", name
        print "urls", urls
        print "queue", queue

    def get_post(self, name, default=""):
        if name in self.post:
            return self.post[name]
        else:
            return default

    def start_response(self, string):

        self.send_response(200)

        self.send_header("Content-Length", len(string))
        self.send_header("Content-Language", "de")
        self.send_header("Vary", "Accept-Language, Cookie")
        self.send_header("Cache-Control", "no-cache, must-revalidate")
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        path = self.path.strip("/").lower()
        #self.wfile.write(path+"\n")

        self.map = [ (r"add$", self.add),
                (r"addcrypted$", self.addcrypted),
                (r"addcrypted2$", self.addcrypted2),
                (r"flashgot", self.flashgot),
                (r"crossdomain\.xml", self.crossdomain),
                (r"checkSupportForUrl", self.checksupport),
                (r"jdcheck.js", self.jdcheck),
                (r"", self.flash) ]

        func = None
        for r, f in self.map:
            if re.match(r"(flash(got)?/?)?"+r, path):
                func = f
                break

        if func:
            try:
                resp = func()
                if not resp: resp = "success"
                resp += "\r\n"
                self.start_response(resp)
                self.wfile.write(resp)
            except Exception,e :
                self.send_error(500, str(e))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        form = FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST',
                         'CONTENT_TYPE':self.headers['Content-Type'],
                         })

        self.post = {}
        for name in form.keys():
            self.post[name] = form[name].value

        return self.do_GET()

    def flash(self):
        return "JDownloader"

    def add(self):
        package = self.get_post('referer', 'ClickAndLoad Package')
        urls = filter(lambda x: x != "", self.get_post('urls').split("\n"))

        self.add_package(package, urls, 0)

    def addcrypted(self):
        package = self.get_post('referer', 'ClickAndLoad Package')
        dlc = self.get_post('crypted').replace(" ", "+")

        core.upload_container(package, dlc)

    def addcrypted2(self):
        package = self.get_post("source", "ClickAndLoad Package")
        crypted = self.get_post("crypted")
        jk = self.get_post("jk")

        crypted = standard_b64decode(unquote(crypted.replace(" ", "+")))
        jk = "%s f()" % jk
        jk = js.eval(jk)
        Key = unhexlify(jk)
        IV = Key

        obj = AES.new(Key, AES.MODE_CBC, IV)
        result = obj.decrypt(crypted).replace("\x00", "").replace("\r","").split("\n")

        result = filter(lambda x: x != "", result)

        self.add_package(package, result, 0)


    def flashgot(self):
        autostart = int(self.get_post('autostart', 0))
        package = self.get_post('package', "FlashGot")
        urls = filter(lambda x: x != "", self.get_post('urls').split("\n"))

        self.add_package(package, urls, autostart)

    def crossdomain(self):
        rep = "<?xml version=\"1.0\"?>\n"
        rep += "<!DOCTYPE cross-domain-policy SYSTEM \"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd\">\n"
        rep += "<cross-domain-policy>\n"
        rep += "<allow-access-from domain=\"*\" />\n"
        rep += "</cross-domain-policy>"
        return rep

    def checksupport(self):
        pass

    def jdcheck(self):
        rep = "jdownloader=true;\n"
        rep += "var version='10629';\n"
        return rep


if __name__ == "__main__":
    import xmlrpclib
    from module import InitHomeDir
    from module.ConfigParser import ConfigParser

    config = ConfigParser()

    ssl = ""
    if config.get("ssl", "activated"):
        ssl = "s"

    server_url = "http%s://%s:%s@%s:%s/" % (
                                        ssl,
                                        config.username,
                                        config.password,
                                        config.get("remote", "listenaddr"),
                                        config.get("remote", "port")
                                        )

    core = xmlrpclib.ServerProxy(server_url, allow_none=True)

    s = CNLServer()
    s.start()
    while not s.stopped:
        try:
            s.join(1)
        except KeyboardInterrupt:
            s.stop = True
            s.stopped = True
            print "quiting.."
