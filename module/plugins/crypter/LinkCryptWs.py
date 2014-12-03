# -*- coding: utf-8 -*-

import base64
import binascii
import re

import pycurl

from Crypto.Cipher import AES

from module.plugins.Crypter import Crypter
from module.utils import html_unescape


class LinkCryptWs(Crypter):
    __name__    = "LinkCryptWs"
    __type__    = "crypter"
    __version__ = "0.07"

    __pattern__ = r'http://(?:www\.)?linkcrypt\.ws/(dir|container)/(?P<ID>\w+)'

    __description__ = """LinkCrypt.ws decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("kagenoshin", "kagenoshin[AT]gmx[DOT]ch"),
                       ("glukgluk", None),
                       ("Gummibaer", None)]


    CRYPTED_KEY = "crypted"
    JK_KEY = "jk"


    def setup(self):
        self.captcha = False
        self.links   = []
        self.sources = ['cnl', 'web', 'dlc', 'rsdf', 'ccf']


    def prepare(self):
        # Init
        self.fileid = re.match(self.__pattern__, self.pyfile.url).group('ID')

        self.req.cj.setCookie("linkcrypt.ws", "language", "en")

        # Request package
        self.req.http.c.setopt(pycurl.USERAGENT, "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko")  #: better chance to not get those key-captchas
        self.html = self.load(self.pyfile.url)


    def decrypt(self, pyfile):
        if not self.js:
            self.fail(_("Missing JS Engine"))

        self.prepare()

        if not self.isOnline():
            self.offline()

        if self.isKeyCaptchaProtected():
            self.retry(4, 30, _("Can't handle Key-Captcha"))

        if self.isCaptchaProtected():
            self.captcha = True
            self.unlockCaptchaProtection()
            self.handleCaptchaErrors()

        # Check for protection
        if self.isPasswordProtected():
            self.unlockPasswordProtection()
            self.handleErrors()

        # get unrar password
        self.getunrarpw()

        # Get package name and folder
        package_name, folder_name = self.getPackageInfo()

        #get the container definitions from script section
        self.get_container_html()

        # Extract package links
        for type in self.sources:
            links = self.handleLinkSource(type)

            if links:
                self.links.extend(links)
                break

        if self.links:
            self.packages = [(package_name, self.links, folder_name)]


    def isOnline(self):
        if "<title>Linkcrypt.ws // Error 404</title>" in self.html:
            self.logDebug("folder doesen't exist anymore")
            return False
        else:
            return True


    def isPasswordProtected(self):
        if "Authorizing" in self.html:
            self.logDebug("Links are password protected")
            return True
        else:
            return False


    def isCaptchaProtected(self):
        if 'id="captcha">' in self.html:
            self.logDebug("Links are captcha protected")
            return True
        else:
            return False


    def isKeyCaptchaProtected(self):
        if re.search(r'Key[ -]', self.html, re.I):
            return True
        else:
            return False


    def unlockPasswordProtection(self):
        password = self.getPassword()

        if password:
            self.logDebug("Submitting password [%s] for protected links" % password)
            self.html = self.load(self.pyfile.url, post={"password": password, 'x': "0", 'y': "0"})
        else:
            self.fail(_("Folder is password protected"))


    def unlockCaptchaProtection(self):
        captcha_url  = re.search(r'<form.*?id\s*?=\s*?"captcha"[^>]*?>.*?<\s*?input.*?src="([^"]*?)"', self.html, re.I | re.S).group(1)
        captcha_code = self.decryptCaptcha(captcha_url, forceUser=True, imgtype="gif", result_type='positional')

        self.html = self.load(self.pyfile.url, post={"x": captcha_code[0], "y": captcha_code[1]})


    def getPackageInfo(self):
        name   = self.pyfile.package().name
        folder = self.pyfile.package().folder

        self.logDebug("Defaulting to pyfile name [%s] and folder [%s] for package" % (name, folder))

        return name, folder


    def getunrarpw(self):
        sitein = self.html
        indexi = sitein.find("|source|") + 8
        indexe = sitein.find("|",indexi)

        unrarpw = sitein[indexi:indexe]

        if not (unrarpw == "Password" or "Dateipasswort") :
            self.logDebug("File password set to: [%s]"% unrarpw)
            self.pyfile.package().password = unrarpw


    def handleErrors(self):
        if self.isPasswordProtected():
            self.fail(_("Incorrect password"))


    def handleCaptchaErrors(self):
        if self.captcha:
            if "Your choice was wrong!" in self.html:
                self.invalidCaptcha()
                self.retry()
            else:
                self.correctCaptcha()


    def handleLinkSource(self, type):
        if type == 'cnl':
                return self.handleCNL2()

        elif type == 'web':
                return self.handleWebLinks()

        elif type in ('rsdf', 'ccf', 'dlc'):
                return self.handleContainer(type)

        else:
            self.fail(_("Unknown source type: %s") % type)  #@TODO: Replace with self.error in 0.4.10


    def handleWebLinks(self):
        self.logDebug("Search for Web links ")

        package_links = []
        pattern = r'<form action="http://linkcrypt.ws/out.html"[^>]*?>.*?<input[^>]*?value="([^"]*?)"[^>]*?name="file"'
        ids = re.findall(pattern, self.html, re.I | re.S)

        self.logDebug("Decrypting %d Web links" % len(ids))

        for idx, weblink_id in enumerate(ids):
            try:
                self.logDebug("Decrypting Web link %d, %s" % (idx + 1, weblink_id))

                res = self.load("http://linkcrypt.ws/out.html", post = {'file':weblink_id})

                indexs = res.find("window.location =") + 19
                indexe = res.find('"', indexs)

                link2 = res[indexs:indexe]

                self.logDebug(link2)

                link2 = html_unescape(link2)
                package_links.append(link2)

            except Exception, detail:
                self.logDebug("Error decrypting Web link %s, %s" % (weblink_id, detail))

        return package_links


    def get_container_html(self):
        self.container_html = []

        script = re.search(r'<div.*?id="ad_cont".*?<script.*?javascrip[^>]*?>(.*?)</script', self.html, re.I | re.S)

        if script:
            container_html_text = script.group(1)
            container_html_text.strip()
            self.container_html = container_html_text.splitlines()


    def handle_javascript(self, line):
        return self.js.eval(line.replace('{}))',"{}).replace('document.open();document.write','').replace(';document.close();',''))"))


    def handleContainer(self, type):
        package_links = []
        type = type.lower()

        self.logDebug('Search for %s Container links' % type.upper())

        if not type.isalnum():  # check to prevent broken re-pattern (cnl2,rsdf,ccf,dlc,web are all alpha-numeric)
            self.fail(_("Unknown container type: %s") % type)  #@TODO: Replace with self.error in 0.4.10

        for line in self.container_html:
            if type in line:
                jseval = self.handle_javascript(line)
                clink = re.search(r'href=["\']([^"\']*?)["\']',jseval,re.I)

                if not clink:
                    continue

                self.logDebug("clink avaible")

                package_name, folder_name = self.getPackageInfo()
                self.logDebug("Added package with name %s.%s and container link %s" %( package_name, type, clink.group(1)))
                self.core.api.uploadContainer( "%s.%s" %(package_name, type), self.load(clink.group(1)))
                return "Found it"

        return package_links


    def handleCNL2(self):
        self.logDebug("Search for CNL links")

        package_links = []
        cnl_line = None

        for line in self.container_html:
            if "cnl" in line:
                cnl_line = line
                break

        if cnl_line:
            self.logDebug("cnl_line gefunden")

        try:
            cnl_section = self.handle_javascript(cnl_line)
            (vcrypted, vjk) = self._getCipherParams(cnl_section)
            for (crypted, jk) in zip(vcrypted, vjk):
                package_links.extend(self._getLinks(crypted, jk))
        except:
            self.logError(_("Unable to decrypt CNL links (JS Error) try to get over links"))
            return self.handleWebLinks()

        return package_links


    def _getCipherParams(self, cnl_section):
        # Get jk
        jk_re = r'<INPUT.*?NAME="%s".*?VALUE="(.*?)"' % LinkCryptWs.JK_KEY
        vjk = re.findall(jk_re, cnl_section)

        # Get crypted
        crypted_re = r'<INPUT.*?NAME="%s".*?VALUE="(.*?)"' % LinkCryptWs.CRYPTED_KEY
        vcrypted = re.findall(crypted_re, cnl_section)

        # Log and return
        self.logDebug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk


    def _getLinks(self, crypted, jk):
        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        key     = binascii.unhexlify(jreturn)

        self.logDebug("JsEngine returns value [%s]" % jreturn)

        # Decode crypted
        crypted = base64.standard_b64decode(crypted)

        # Decrypt
        Key  = key
        IV   = key
        obj  = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted)

        # Extract links
        text  = text.replace("\x00", "").replace("\r", "")
        links = text.split("\n")
        links = filter(lambda x: x != "", links)

        # Log and return
        self.logDebug("Package has %d links" % len(links))

        return links
