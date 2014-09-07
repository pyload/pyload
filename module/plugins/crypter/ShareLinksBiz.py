# -*- coding: utf-8 -*-

import base64
import binascii
import re

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter


class ShareLinksBiz(Crypter):
    __name__ = "ShareLinksBiz"
    __type__ = "crypter"
    __version__ = "1.13"

    __pattern__ = r'http://(?:www\.)?(share-links|s2l)\.biz/(?P<ID>_?\w+)'

    __description__ = """Share-Links.biz decrypter plugin"""
    __author_name__ = "fragonib"
    __author_mail__ = "fragonib[AT]yahoo[DOT]es"


    def setup(self):
        self.baseUrl = None
        self.fileId = None
        self.package = None
        self.html = None
        self.captcha = False

    def decrypt(self, pyfile):
        # Init
        self.initFile(pyfile)

        # Request package
        url = self.baseUrl + '/' + self.fileId
        self.html = self.load(url, decode=True)

        # Unblock server (load all images)
        self.unblockServer()

        # Check for protection
        if self.isPasswordProtected():
            self.unlockPasswordProtection()
            self.handleErrors()

        if self.isCaptchaProtected():
            self.captcha = True
            self.unlockCaptchaProtection()
            self.handleErrors()

        # Extract package links
        package_links = []
        package_links.extend(self.handleWebLinks())
        package_links.extend(self.handleContainers())
        package_links.extend(self.handleCNL2())
        package_links = set(package_links)

        # Get package info
        package_name, package_folder = self.getPackageInfo()

        # Pack
        self.packages = [(package_name, package_links, package_folder)]

    def initFile(self, pyfile):
        url = pyfile.url
        if 's2l.biz' in url:
            url = self.load(url, just_header=True)['location']
        self.baseUrl = "http://www.%s.biz" % re.match(self.__pattern__, url).group(1)
        self.fileId = re.match(self.__pattern__, url).group('ID')
        self.package = pyfile.package()

    def isOnline(self):
        if "No usable content was found" in self.html:
            self.logDebug("File not found")
            return False
        return True

    def isPasswordProtected(self):
        if re.search(r'''<form.*?id="passwordForm".*?>''', self.html):
            self.logDebug("Links are protected")
            return True
        return False

    def isCaptchaProtected(self):
        if '<map id="captchamap"' in self.html:
            self.logDebug("Links are captcha protected")
            return True
        return False

    def unblockServer(self):
        imgs = re.findall(r"(/template/images/.*?\.gif)", self.html)
        for img in imgs:
            self.load(self.baseUrl + img)

    def unlockPasswordProtection(self):
        password = self.getPassword()
        self.logDebug("Submitting password [%s] for protected links" % password)
        post = {"password": password, 'login': 'Submit form'}
        url = self.baseUrl + '/' + self.fileId
        self.html = self.load(url, post=post, decode=True)

    def unlockCaptchaProtection(self):
        # Get captcha map
        captchaMap = self._getCaptchaMap()
        self.logDebug("Captcha map with [%d] positions" % len(captchaMap.keys()))

        # Request user for captcha coords
        m = re.search(r'<img src="/captcha.gif\?d=(.*?)&amp;PHPSESSID=(.*?)&amp;legend=1"', self.html)
        captchaUrl = self.baseUrl + '/captcha.gif?d=%s&PHPSESSID=%s' % (m.group(1), m.group(2))
        self.logDebug("Waiting user for correct position")
        coords = self.decryptCaptcha(captchaUrl, forceUser=True, imgtype="gif", result_type='positional')
        self.logDebug("Captcha resolved, coords [%s]" % str(coords))

        # Resolve captcha
        href = self._resolveCoords(coords, captchaMap)
        if href is None:
            self.logDebug("Invalid captcha resolving, retrying")
            self.invalidCaptcha()
            self.setWait(5, False)
            self.wait()
            self.retry()
        url = self.baseUrl + href
        self.html = self.load(url, decode=True)

    def _getCaptchaMap(self):
        mapp = {}
        for m in re.finditer(r'<area shape="rect" coords="(.*?)" href="(.*?)"', self.html):
            rect = eval('(' + m.group(1) + ')')
            href = m.group(2)
            mapp[rect] = href
        return mapp

    def _resolveCoords(self, coords, captchaMap):
        x, y = coords
        for rect, href in captchaMap.items():
            x1, y1, x2, y2 = rect
            if (x >= x1 and x <= x2) and (y >= y1 and y <= y2):
                return href

    def handleErrors(self):
        if "The inserted password was wrong" in self.html:
            self.logDebug("Incorrect password, please set right password on 'Edit package' form and retry")
            self.fail("Incorrect password, please set right password on 'Edit package' form and retry")

        if self.captcha:
            if "Your choice was wrong" in self.html:
                self.logDebug("Invalid captcha, retrying")
                self.invalidCaptcha()
                self.setWait(5)
                self.wait()
                self.retry()
            else:
                self.correctCaptcha()

    def getPackageInfo(self):
        name = folder = None

        # Extract from web package header
        title_re = r'<h2><img.*?/>(.*)</h2>'
        m = re.search(title_re, self.html, re.DOTALL)
        if m is not None:
            title = m.group(1).strip()
            if 'unnamed' not in title:
                name = folder = title
                self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))

        # Fallback to defaults
        if not name or not folder:
            name = self.package.name
            folder = self.package.folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))

        # Return package info
        return name, folder

    def handleWebLinks(self):
        package_links = []
        self.logDebug("Handling Web links")

        #@TODO: Gather paginated web links
        pattern = r"javascript:_get\('(.*?)', \d+, ''\)"
        ids = re.findall(pattern, self.html)
        self.logDebug("Decrypting %d Web links" % len(ids))
        for i, ID in enumerate(ids):
            try:
                self.logDebug("Decrypting Web link %d, [%s]" % (i + 1, ID))
                dwLink = self.baseUrl + "/get/lnk/" + ID
                response = self.load(dwLink)
                code = re.search(r'frm/(\d+)', response).group(1)
                fwLink = self.baseUrl + "/get/frm/" + code
                response = self.load(fwLink)
                jscode = re.search(r'<script language="javascript">\s*eval\((.*)\)\s*</script>', response,
                                   re.DOTALL).group(1)
                jscode = self.js.eval("f = %s" % jscode)
                jslauncher = "window=''; parent={frames:{Main:{location:{href:''}}},location:''}; %s; parent.frames.Main.location.href"
                dlLink = self.js.eval(jslauncher % jscode)
                self.logDebug("JsEngine returns value [%s] for redirection link" % dlLink)
                package_links.append(dlLink)
            except Exception, detail:
                self.logDebug("Error decrypting Web link [%s], %s" % (ID, detail))
        return package_links

    def handleContainers(self):
        package_links = []
        self.logDebug("Handling Container links")

        pattern = r"javascript:_get\('(.*?)', 0, '(rsdf|ccf|dlc)'\)"
        containersLinks = re.findall(pattern, self.html)
        self.logDebug("Decrypting %d Container links" % len(containersLinks))
        for containerLink in containersLinks:
            link = "%s/get/%s/%s" % (self.baseUrl, containerLink[1], containerLink[0])
            package_links.append(link)
        return package_links

    def handleCNL2(self):
        package_links = []
        self.logDebug("Handling CNL2 links")

        if '/lib/cnl2/ClicknLoad.swf' in self.html:
            try:
                (crypted, jk) = self._getCipherParams()
                package_links.extend(self._getLinks(crypted, jk))
            except:
                self.fail("Unable to decrypt CNL2 links")
        return package_links

    def _getCipherParams(self):
        # Request CNL2
        code = re.search(r'ClicknLoad.swf\?code=(.*?)"', self.html).group(1)
        url = "%s/get/cnl2/%s" % (self.baseUrl, code)
        response = self.load(url)
        params = response.split(";;")

        # Get jk
        strlist = list(base64.standard_b64decode(params[1]))
        strlist.reverse()
        jk = ''.join(strlist)

        # Get crypted
        strlist = list(base64.standard_b64decode(params[2]))
        strlist.reverse()
        crypted = ''.join(strlist)

        # Log and return
        return crypted, jk

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
        self.logDebug("Block has %d links" % len(links))
        return links
