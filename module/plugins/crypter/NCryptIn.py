# -*- coding: utf-8 -*-

import base64
import binascii
import re

from Crypto.Cipher import AES

from module.plugins.Crypter import Crypter
from module.plugins.internal.CaptchaService import ReCaptcha


class NCryptIn(Crypter):
    __name__ = "NCryptIn"
    __type__ = "crypter"
    __version__ = "1.32"

    __pattern__ = r'http://(?:www\.)?ncrypt.in/(?P<type>folder|link|frame)-([^/\?]+)'

    __description__ = """NCrypt.in decrypter plugin"""
    __author_name__ = ("fragonib", "stickell")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "l.stickell@yahoo.it")

    JK_KEY = "jk"
    CRYPTED_KEY = "crypted"

    NAME_PATTERN = r'<meta name="description" content="(?P<N>[^"]+)"'


    def setup(self):
        self.package = None
        self.html = None
        self.cleanedHtml = None
        self.links_source_order = ["cnl2", "rsdf", "ccf", "dlc", "web"]
        self.protection_type = None

    def decrypt(self, pyfile):
        # Init
        self.package = pyfile.package()
        package_links = []
        package_name = self.package.name
        folder_name = self.package.folder

        # Deal with single links
        if self.isSingleLink():
            package_links.extend(self.handleSingleLink())

        # Deal with folders
        else:

            # Request folder home
            self.html = self.requestFolderHome()
            self.cleanedHtml = self.removeHtmlCrap(self.html)
            if not self.isOnline():
                self.offline()

            # Check for folder protection
            if self.isProtected():
                self.html = self.unlockProtection()
                self.cleanedHtml = self.removeHtmlCrap(self.html)
                self.handleErrors()

            # Prepare package name and folder
            (package_name, folder_name) = self.getPackageInfo()

            # Extract package links
            for link_source_type in self.links_source_order:
                package_links.extend(self.handleLinkSource(link_source_type))
                if package_links:  # use only first source which provides links
                    break
            package_links = set(package_links)

        # Pack and return links
        if not package_links:
            self.fail('Could not extract any links')
        self.packages = [(package_name, package_links, folder_name)]

    def isSingleLink(self):
        link_type = re.match(self.__pattern__, self.pyfile.url).group('type')
        return link_type in ("link", "frame")

    def requestFolderHome(self):
        return self.load(self.pyfile.url, decode=True)

    def removeHtmlCrap(self, content):
        patterns = (r'(type="hidden".*?(name=".*?")?.*?value=".*?")',
                    r'display:none;">(.*?)</(div|span)>',
                    r'<div\s+class="jdownloader"(.*?)</div>',
                    r'<table class="global">(.*?)</table>',
                    r'<iframe\s+style="display:none(.*?)</iframe>')
        for pattern in patterns:
            rexpr = re.compile(pattern, re.DOTALL)
            content = re.sub(rexpr, "", content)
        return content

    def isOnline(self):
        if "Your folder does not exist" in self.cleanedHtml:
            self.logDebug("File not m")
            return False
        return True

    def isProtected(self):
        form = re.search(r'<form.*?name.*?protected.*?>(.*?)</form>', self.cleanedHtml, re.DOTALL)
        if form is not None:
            content = form.group(1)
            for keyword in ("password", "captcha"):
                if keyword in content:
                    self.protection_type = keyword
                    self.logDebug("Links are %s protected" % self.protection_type)
                    return True
        return False

    def getPackageInfo(self):
        m = re.search(self.NAME_PATTERN, self.html)
        if m:
            name = folder = m.group('N').strip()
            self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))
        else:
            name = self.package.name
            folder = self.package.folder
            self.logDebug("Package info not m, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder

    def unlockProtection(self):

        postData = {}

        form = re.search(r'<form name="protected"(.*?)</form>', self.cleanedHtml, re.DOTALL).group(1)

        # Submit package password
        if "password" in form:
            password = self.getPassword()
            self.logDebug("Submitting password [%s] for protected links" % password)
            postData['password'] = password

        # Resolve anicaptcha
        if "anicaptcha" in form:
            self.logDebug("Captcha protected")
            captchaUri = re.search(r'src="(/temp/anicaptcha/[^"]+)', form).group(1)
            captcha = self.decryptCaptcha("http://ncrypt.in" + captchaUri)
            self.logDebug("Captcha resolved [%s]" % captcha)
            postData['captcha'] = captcha

        # Resolve recaptcha
        if "recaptcha" in form:
            self.logDebug("ReCaptcha protected")
            captcha_key = re.search(r'\?k=(.*?)"', form).group(1)
            self.logDebug("Resolving ReCaptcha with key [%s]" % captcha_key)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(captcha_key)
            postData['recaptcha_challenge_field'] = challenge
            postData['recaptcha_response_field'] = code

        # Resolve circlecaptcha
        if "circlecaptcha" in form:
            self.logDebug("CircleCaptcha protected")
            captcha_img_url = "http://ncrypt.in/classes/captcha/circlecaptcha.php"
            coords = self.decryptCaptcha(captcha_img_url, forceUser=True, imgtype="png", result_type='positional')
            self.logDebug("Captcha resolved, coords [%s]" % str(coords))
            postData['circle.x'] = coords[0]
            postData['circle.y'] = coords[1]

        # Unlock protection
        postData['submit_protected'] = 'Continue to folder'
        return self.load(self.pyfile.url, post=postData, decode=True)

    def handleErrors(self):
        if self.protection_type == "password":
            if "This password is invalid!" in self.cleanedHtml:
                self.logDebug("Incorrect password, please set right password on 'Edit package' form and retry")
                self.fail("Incorrect password, please set right password on 'Edit package' form and retry")

        if self.protection_type == "captcha":
            if "The securitycheck was wrong!" in self.cleanedHtml:
                self.logDebug("Invalid captcha, retrying")
                self.invalidCaptcha()
                self.retry()
            else:
                self.correctCaptcha()

    def handleLinkSource(self, link_source_type):
        # Check for JS engine
        require_js_engine = link_source_type in ("cnl2", "rsdf", "ccf", "dlc")
        if require_js_engine and not self.js:
            self.logDebug("No JS engine available, skip %s links" % link_source_type)
            return []

        # Select suitable handler
        if link_source_type == 'single':
            return self.handleSingleLink()
        if link_source_type == 'cnl2':
            return self.handleCNL2()
        elif link_source_type in ("rsdf", "ccf", "dlc"):
            return self.handleContainer(link_source_type)
        elif link_source_type == "web":
            return self.handleWebLinks()
        else:
            self.fail('unknown source type "%s" (this is probably a bug)' % link_source_type)

    def handleSingleLink(self):

        self.logDebug("Handling Single link")
        package_links = []

        # Decrypt single link
        decrypted_link = self.decryptLink(self.pyfile.url)
        if decrypted_link:
            package_links.append(decrypted_link)

        return package_links

    def handleCNL2(self):

        self.logDebug("Handling CNL2 links")
        package_links = []

        if 'cnl2_output' in self.cleanedHtml:
            try:
                (vcrypted, vjk) = self._getCipherParams()
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except:
                self.fail("Unable to decrypt CNL2 links")

        return package_links

    def handleContainers(self):

        self.logDebug("Handling Container links")
        package_links = []

        pattern = r"/container/(rsdf|dlc|ccf)/([a-z0-9]+)"
        containersLinks = re.findall(pattern, self.html)
        self.logDebug("Decrypting %d Container links" % len(containersLinks))
        for containerLink in containersLinks:
            link = "http://ncrypt.in/container/%s/%s.%s" % (containerLink[0], containerLink[1], containerLink[0])
            package_links.append(link)

        return package_links

    def handleWebLinks(self):

        self.logDebug("Handling Web links")
        pattern = r"(http://ncrypt\.in/link-.*?=)"
        links = re.findall(pattern, self.html)

        package_links = []
        self.logDebug("Decrypting %d Web links" % len(links))
        for i, link in enumerate(links):
            self.logDebug("Decrypting Web link %d, %s" % (i + 1, link))
            decrypted_link = self.decrypt(link)
            if decrypted_link:
                package_links.append(decrypted_link)

        return package_links

    def decryptLink(self, link):
        try:
            url = link.replace("link-", "frame-")
            link = self.load(url, just_header=True)['location']
            return link
        except Exception, detail:
            self.logDebug("Error decrypting link %s, %s" % (link, detail))

    def _getCipherParams(self):

        pattern = r'<input.*?name="%s".*?value="(.*?)"'

        # Get jk
        jk_re = pattern % NCryptIn.JK_KEY
        vjk = re.findall(jk_re, self.html)

        # Get crypted
        crypted_re = pattern % NCryptIn.CRYPTED_KEY
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
        self.logDebug("Block has %d links" % len(links))
        return links
