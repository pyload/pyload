# -*- coding: utf-8 -*-

from __future__ import with_statement

import binascii
import re
import os

from Crypto.Cipher import AES
from module.plugins.internal.Crypter import Crypter
from module.utils import save_join


class RelinkUs(Crypter):
    __name__    = "RelinkUs"
    __type__    = "crypter"
    __version__ = "3.13"

    __pattern__ = r'http://(?:www\.)?relink\.us/(f/|((view|go)\.php\?id=))(?P<ID>.+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Relink.us decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("AndroKev", "neureither.kevin@gmail.com")]


    PREFERRED_LINK_SOURCES = ["cnl2", "dlc", "web"]

    OFFLINE_TOKEN = r'<title>Tattooside'

    PASSWORD_TOKEN = r'container_password.php'
    PASSWORD_ERROR_ROKEN = r'You have entered an incorrect password'
    PASSWORD_SUBMIT_URL = r'http://www.relink.us/container_password.php'

    CAPTCHA_TOKEN = r'container_captcha.php'
    CAPTCHA_ERROR_ROKEN = r'You have solved the captcha wrong'
    CAPTCHA_IMG_URL = r'http://www.relink.us/core/captcha/circlecaptcha.php'
    CAPTCHA_SUBMIT_URL = r'http://www.relink.us/container_captcha.php'

    FILE_TITLE_REGEX = r'<th>Title</th><td>(.*)</td></tr>'
    FILE_NOTITLE = r'No title'

    CNL2_FORM_REGEX = r'<form id="cnl_form-(.*?)</form>'
    CNL2_FORMINPUT_REGEX = r'<input.*?name="%s".*?value="(.*?)"'
    CNL2_JK_KEY = "jk"
    CNL2_CRYPTED_KEY = "crypted"

    DLC_LINK_REGEX = r'<a href=".*?" class="dlc_button" target="_blank">'
    DLC_DOWNLOAD_URL = r'http://www.relink.us/download.php'

    WEB_FORWARD_REGEX = r'getFile\(\'(.+)\'\)'
    WEB_FORWARD_URL = r'http://www.relink.us/frame.php'
    WEB_LINK_REGEX = r'<iframe name="Container" height="100%" frameborder="no" width="100%" src="(.+)"></iframe>'


    def setup(self):
        self.fileid  = None
        self.package = None
        self.captcha = False


    def decrypt(self, pyfile):
        # Init
        self.initPackage(pyfile)

        # Request package
        self.requestPackage()

        # Check for online
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
        for sources in self.PREFERRED_LINK_SOURCES:
            package_links.extend(self.handleLinkSource(sources))
            if package_links:  # use only first source which provides links
                break
        package_links = set(package_links)

        # Pack
        if package_links:
            self.packages = [(package_name, package_links, folder_name)]


    def initPackage(self, pyfile):
        self.fileid = re.match(self.__pattern__, pyfile.url).group('ID')
        self.package = pyfile.package()


    def requestPackage(self):
        self.html = self.load(self.pyfile.url, decode=True)


    def isOnline(self):
        if self.OFFLINE_TOKEN in self.html:
            self.logDebug("File not found")
            return False
        return True


    def isPasswordProtected(self):
        if self.PASSWORD_TOKEN in self.html:
            self.logDebug("Links are password protected")
            return True


    def isCaptchaProtected(self):
        if self.CAPTCHA_TOKEN in self.html:
            self.logDebug("Links are captcha protected")
            return True
        return False


    def unlockPasswordProtection(self):
        password = self.getPassword()

        self.logDebug("Submitting password [%s] for protected links" % password)

        if password:
            passwd_url = self.PASSWORD_SUBMIT_URL + "?id=%s" % self.fileid
            passwd_data = {'id': self.fileid, 'password': password, 'pw': 'submit'}
            self.html = self.load(passwd_url, post=passwd_data, decode=True)


    def unlockCaptchaProtection(self):
        self.logDebug("Request user positional captcha resolving")
        captcha_img_url = self.CAPTCHA_IMG_URL + "?id=%s" % self.fileid
        coords = self.decryptCaptcha(captcha_img_url, forceUser=True, imgtype="png", result_type='positional')
        self.logDebug("Captcha resolved, coords [%s]" % str(coords))
        captcha_post_url = self.CAPTCHA_SUBMIT_URL + "?id=%s" % self.fileid
        captcha_post_data = {'button.x': coords[0], 'button.y': coords[1], 'captcha': 'submit'}
        self.html = self.load(captcha_post_url, post=captcha_post_data, decode=True)


    def getPackageInfo(self):
        name = folder = None

        # Try to get info from web
        m = re.search(self.FILE_TITLE_REGEX, self.html)
        if m:
            title = m.group(1).strip()
            if not self.FILE_NOTITLE in title:
                name = folder = title
                self.logDebug("Found name [%s] and folder [%s] in package info" % (name, folder))

        # Fallback to defaults
        if not name or not folder:
            name = self.package.name
            folder = self.package.folder
            self.logDebug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))

        # Return package info
        return name, folder


    def handleErrors(self):
        if self.PASSWORD_ERROR_ROKEN in self.html:
            msg = "Incorrect password, please set right password on 'Edit package' form and retry"
            self.logDebug(msg)
            self.fail(_(msg))

        if self.captcha:
            if self.CAPTCHA_ERROR_ROKEN in self.html:
                self.invalidCaptcha()
                self.retry()
            else:
                self.correctCaptcha()


    def handleLinkSource(self, source):
        if source == 'cnl2':
            return self.handleCNL2Links()
        elif source == 'dlc':
            return self.handleDLCLinks()
        elif source == 'web':
            return self.handleWEBLinks()
        else:
            self.error(_('Unknown source type "%s"') % source)


    def handleCNL2Links(self):
        self.logDebug("Search for CNL2 links")
        package_links = []
        m = re.search(self.CNL2_FORM_REGEX, self.html, re.S)
        if m:
            cnl2_form = m.group(1)
            try:
                (vcrypted, vjk) = self._getCipherParams(cnl2_form)
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except Exception:
                self.logDebug("Unable to decrypt CNL2 links")
        return package_links


    def handleDLCLinks(self):
        self.logDebug("Search for DLC links")
        package_links = []
        m = re.search(self.DLC_LINK_REGEX, self.html)
        if m:
            container_url = self.DLC_DOWNLOAD_URL + "?id=%s&dlc=1" % self.fileid
            self.logDebug("Downloading DLC container link [%s]" % container_url)
            try:
                dlc = self.load(container_url)
                dlc_filename = self.fileid + ".dlc"
                dlc_filepath = save_join(self.config['general']['download_folder'], dlc_filename)
                with open(dlc_filepath, "wb") as f:
                    f.write(dlc)
                package_links.append(dlc_filepath)

            except Exception:
                self.fail(_("Unable to download DLC container"))

        return package_links


    def handleWEBLinks(self):
        self.logDebug("Search for WEB links")

        package_links = []
        params        = re.findall(self.WEB_FORWARD_REGEX, self.html)

        self.logDebug("Decrypting %d Web links" % len(params))

        for index, param in enumerate(params):
            try:
                url = self.WEB_FORWARD_URL + "?%s" % param

                self.logDebug("Decrypting Web link %d, %s" % (index + 1, url))

                res  = self.load(url, decode=True)
                link = re.search(self.WEB_LINK_REGEX, res).group(1)

                package_links.append(link)

            except Exception, detail:
                self.logDebug("Error decrypting Web link %s, %s" % (index, detail))

            self.setWait(4)
            self.wait()

        return package_links


    def _getCipherParams(self, cnl2_form):
        # Get jk
        jk_re = self.CNL2_FORMINPUT_REGEX % self.CNL2_JK_KEY
        vjk = re.findall(jk_re, cnl2_form, re.I)

        # Get crypted
        crypted_re = self.CNL2_FORMINPUT_REGEX % RelinkUs.CNL2_CRYPTED_KEY
        vcrypted = re.findall(crypted_re, cnl2_form, re.I)

        # Log and return
        self.logDebug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk


    def _getLinks(self, crypted, jk):
        # Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.logDebug("JsEngine returns value [%s]" % jreturn)
        key = binascii.unhexlify(jreturn)

        # Decrypt
        Key = key
        IV = key
        obj = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        # Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        # Log and return
        self.logDebug("Package has %d links" % len(links))
        return links
