# -*- coding: utf-8 -*-
#
# * cnl2 and web links are skipped if JS is not available (instead of failing the package)
# * only best available link source is used (priority: cnl2>rsdf>ccf>dlc>web

import base64
import binascii
import re

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter
from module.unescape import unescape


class LinkSaveIn(Crypter):
    __name__ = "LinkSaveIn"
    __type__ = "crypter"
    __version__ = "2.01"

    __pattern__ = r'http://(?:www\.)?linksave.in/(?P<id>\w+)$'

    __description__ = """LinkSave.in decrypter plugin"""
    __author_name__ = "fragonib"
    __author_mail__ = "fragonib[AT]yahoo[DOT]es"

    # Constants
    _JK_KEY_ = "jk"
    _CRYPTED_KEY_ = "crypted"
    HOSTER_NAME = "linksave.in"


    def setup(self):
        self.html = None
        self.fileid = None
        self.captcha = False
        self.package = None
        self.preferred_sources = ["cnl2", "rsdf", "ccf", "dlc", "web"]

    def decrypt(self, pyfile):
        # Init
        self.package = pyfile.package()
        self.fileid = re.match(self.__pattern__, pyfile.url).group('id')
        self.req.cj.setCookie(self.HOSTER_NAME, "Linksave_Language", "english")

        # Request package
        self.html = self.load(pyfile.url)
        if not self.isOnline():
            self.offline()

        # Check for protection
        if self.isPasswordProtected():
            self.unlockPasswordProtection()
            self.handleErrors()

        if self.isCaptchaProtected():
            self.captcha = True
            self.unlockCaptchaProtection()
            self.handleErrors()

        # Get package name and folder
        (package_name, folder_name) = self.getPackageInfo()

        # Extract package links
        package_links = []
        for type_ in self.preferred_sources:
            package_links.extend(self.handleLinkSource(type_))
            if package_links:  # use only first source which provides links
                break
        package_links = set(package_links)

        # Pack
        if package_links:
            self.packages = [(package_name, package_links, folder_name)]
        else:
            self.fail('Could not extract any links')

    def isOnline(self):
        if "<big>Error 404 - Folder not found!</big>" in self.html:
            self.logDebug("File not found")
            return False
        return True

    def isPasswordProtected(self):
        if re.search(r'''<input.*?type="password"''', self.html):
            self.logDebug("Links are password protected")
            return True

    def isCaptchaProtected(self):
        if "<b>Captcha:</b>" in self.html:
            self.logDebug("Links are captcha protected")
            return True
        return False

    def unlockPasswordProtection(self):
        password = self.getPassword()
        self.logDebug("Submitting password [%s] for protected links" % password)
        post = {"id": self.fileid, "besucherpasswort": password, 'login': 'submit'}
        self.html = self.load(self.pyfile.url, post=post)

    def unlockCaptchaProtection(self):
        captcha_hash = re.search(r'name="hash" value="([^"]+)', self.html).group(1)
        captcha_url = re.search(r'src=".(/captcha/cap.php\?hsh=[^"]+)', self.html).group(1)
        captcha_code = self.decryptCaptcha("http://linksave.in" + captcha_url, forceUser=True)
        self.html = self.load(self.pyfile.url, post={"id": self.fileid, "hash": captcha_hash, "code": captcha_code})

    def getPackageInfo(self):
        name = self.pyfile.package().name
        folder = self.pyfile.package().folder
        self.logDebug("Defaulting to pyfile name [%s] and folder [%s] for package" % (name, folder))
        return name, folder

    def handleErrors(self):
        if "The visitorpassword you have entered is wrong" in self.html:
            self.logDebug("Incorrect password, please set right password on 'Edit package' form and retry")
            self.fail("Incorrect password, please set right password on 'Edit package' form and retry")

        if self.captcha:
            if "Wrong code. Please retry" in self.html:
                self.logDebug("Invalid captcha, retrying")
                self.invalidCaptcha()
                self.retry()
            else:
                self.correctCaptcha()

    def handleLinkSource(self, type_):
        if type_ == "cnl2":
            return self.handleCNL2()
        elif type_ in ("rsdf", "ccf", "dlc"):
            return self.handleContainer(type_)
        elif type_ == "web":
            return self.handleWebLinks()
        else:
            self.fail('unknown source type "%s" (this is probably a bug)' % type_)

    def handleWebLinks(self):
        package_links = []
        self.logDebug("Search for Web links")
        if not self.js:
            self.logDebug("no JS -> skip Web links")
        else:
        #@TODO: Gather paginated web links
            pattern = r'<a href="http://linksave\.in/(\w{43})"'
            ids = re.findall(pattern, self.html)
            self.logDebug("Decrypting %d Web links" % len(ids))
            for i, weblink_id in enumerate(ids):
                try:
                    webLink = "http://linksave.in/%s" % weblink_id
                    self.logDebug("Decrypting Web link %d, %s" % (i + 1, webLink))
                    fwLink = "http://linksave.in/fw-%s" % weblink_id
                    response = self.load(fwLink)
                    jscode = re.findall(r'<script type="text/javascript">(.*)</script>', response)[-1]
                    jseval = self.js.eval("document = { write: function(e) { return e; } }; %s" % jscode)
                    dlLink = re.search(r'http://linksave\.in/dl-\w+', jseval).group(0)
                    self.logDebug("JsEngine returns value [%s] for redirection link" % dlLink)
                    response = self.load(dlLink)
                    link = unescape(re.search(r'<iframe src="(.+?)"', response).group(1))
                    package_links.append(link)
                except Exception, detail:
                    self.logDebug("Error decrypting Web link %s, %s" % (webLink, detail))
        return package_links

    def handleContainer(self, type_):
        package_links = []
        type_ = type_.lower()
        self.logDebug('Seach for %s Container links' % type_.upper())
        if not type_.isalnum():  # check to prevent broken re-pattern (cnl2,rsdf,ccf,dlc,web are all alpha-numeric)
            self.fail('unknown container type "%s" (this is probably a bug)' % type_)
        pattern = r"\('%s_link'\).href=unescape\('(.*?\.%s)'\)" % (type_, type_)
        containersLinks = re.findall(pattern, self.html)
        self.logDebug("Found %d %s Container links" % (len(containersLinks), type_.upper()))
        for containerLink in containersLinks:
            link = "http://linksave.in/%s" % unescape(containerLink)
            package_links.append(link)
        return package_links

    def handleCNL2(self):
        package_links = []
        self.logDebug("Search for CNL2 links")
        if not self.js:
            self.logDebug("no JS -> skip CNL2 links")
        elif 'cnl2_load' in self.html:
            try:
                (vcrypted, vjk) = self._getCipherParams()
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except:
                self.fail("Unable to decrypt CNL2 links")
        return package_links

    def _getCipherParams(self):
        # Get jk
        jk_re = r'<INPUT.*?NAME="%s".*?VALUE="(.*?)"' % LinkSaveIn._JK_KEY_
        vjk = re.findall(jk_re, self.html)

        # Get crypted
        crypted_re = r'<INPUT.*?NAME="%s".*?VALUE="(.*?)"' % LinkSaveIn._CRYPTED_KEY_
        vcrypted = re.findall(crypted_re, self.html)

        # Log and return
        self.logDebug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk

    def _getLinks(self, crypted, jk):
        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.logDebug("JsEngine returns value [%s]" % jreturn)
        key = binascii.unhexlify(jreturn)

        # Decode crypted
        crypted = base64.standard_b64decode(crypted)

        # Decrypt
        Key = key
        IV = key
        obj = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted)

        # Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = text.split("\n")
        links = filter(lambda x: x != "", links)

        # Log and return
        self.logDebug("Package has %d links" % len(links))
        return links
