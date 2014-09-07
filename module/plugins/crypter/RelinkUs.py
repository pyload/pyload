# -*- coding: utf-8 -*-

import base64
import binascii
import re
import os

from Crypto.Cipher import AES
from module.plugins.Crypter import Crypter


class RelinkUs(Crypter):
    __name__ = "RelinkUs"
    __type__ = "crypter"
    __version__ = "3.0"

    __pattern__ = r'http://(?:www\.)?relink.us/(f/|((view|go).php\?id=))(?P<id>.+)'

    __description__ = """Relink.us decrypter plugin"""
    __author_name__ = "fragonib"
    __author_mail__ = "fragonib[AT]yahoo[DOT]es"

    # Constants
    PREFERRED_LINK_SOURCES = ["cnl2", "dlc", "web"]

    OFFLINE_TOKEN = r'<title>Tattooside'
    PASSWORD_TOKEN = r'container_password\.php'
    PASSWORD_ERROR_ROKEN = r'You have entered an incorrect password'
    PASSWORD_SUBMIT_URL = r'http://www\.relink\.us/container_password\.php'
    CAPTCHA_TOKEN = r'container_captcha\.php'
    CAPTCHA_ERROR_ROKEN = r'You have solved the captcha wrong'
    CAPTCHA_IMG_URL = r'http://www\.relink\.us/core/captcha/circlecaptcha\.php'
    CAPTCHA_SUBMIT_URL = r'http://www\.relink\.us/container_captcha\.php'
    FILE_TITLE_REGEX = r'<th>Title</th><td><i>(.*)</i></td></tr>'
    FILE_NOTITLE = r'No title'

    CNL2_FORM_REGEX = r'<form id="cnl_form-(.*?)</form>'
    CNL2_FORMINPUT_REGEX = r'<input.*?name="%s".*?value="(.*?)"'
    CNL2_JK_KEY = "jk"
    CNL2_CRYPTED_KEY = "crypted"
    DLC_LINK_REGEX = r'<a href=".*?" class="dlc_button" target="_blank">'
    DLC_DOWNLOAD_URL = r'http://www\.relink\.us/download\.php'
    WEB_FORWARD_REGEX = r"getFile\('(?P<link>.+)'\)"
    WEB_FORWARD_URL = r'http://www\.relink\.us/frame\.php'
    WEB_LINK_REGEX = r'<iframe name="Container" height="100%" frameborder="no" width="100%" src="(?P<link>.+)"></iframe>'


    def setup(self):
        self.fileid = None
        self.package = None
        self.password = None
        self.html = None
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
        else:
            self.fail('Could not extract any links')

    def initPackage(self, pyfile):
        self.fileid = re.match(self.__pattern__, pyfile.url).group('id')
        self.package = pyfile.package()
        self.password = self.getPassword()

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
        self.logDebug("Submitting password [%s] for protected links" % self.password)
        passwd_url = self.PASSWORD_SUBMIT_URL + "?id=%s" % self.fileid
        passwd_data = {'id': self.fileid, 'password': self.password, 'pw': 'submit'}
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
        if m is not None:
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
            self.fail(msg)

        if self.captcha:
            if self.CAPTCHA_ERROR_ROKEN in self.html:
                self.logDebug("Invalid captcha, retrying")
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
            self.fail('Unknown source [%s] (this is probably a bug)' % source)

    def handleCNL2Links(self):
        self.logDebug("Search for CNL2 links")
        package_links = []
        m = re.search(self.CNL2_FORM_REGEX, self.html, re.DOTALL)
        if m is not None:
            cnl2_form = m.group(1)
            try:
                (vcrypted, vjk) = self._getCipherParams(cnl2_form)
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._getLinks(crypted, jk))
            except:
                self.logDebug("Unable to decrypt CNL2 links")
        return package_links

    def handleDLCLinks(self):
        self.logDebug('Search for DLC links')
        package_links = []
        m = re.search(self.DLC_LINK_REGEX, self.html)
        if m is not None:
            container_url = self.DLC_DOWNLOAD_URL + "?id=%s&dlc=1" % self.fileid
            self.logDebug("Downloading DLC container link [%s]" % container_url)
            try:
                dlc = self.load(container_url)
                dlc_filename = self.fileid + ".dlc"
                dlc_filepath = os.path.join(self.config['general']['download_folder'], dlc_filename)
                f = open(dlc_filepath, "wb")
                f.write(dlc)
                f.close()
                package_links.append(dlc_filepath)
            except:
                self.logDebug("Unable to download DLC container")
        return package_links

    def handleWEBLinks(self):
        self.logDebug("Search for WEB links")
        package_links = []
        fw_params = re.findall(self.WEB_FORWARD_REGEX, self.html)
        self.logDebug("Decrypting %d Web links" % len(fw_params))
        for index, fw_param in enumerate(fw_params):
            try:
                fw_url = self.WEB_FORWARD_URL + "?%s" % fw_param
                self.logDebug("Decrypting Web link %d, %s" % (index + 1, fw_url))
                fw_response = self.load(fw_url, decode=True)
                dl_link = re.search(self.WEB_LINK_REGEX, fw_response).group('link')
                package_links.append(dl_link)
            except Exception, detail:
                self.logDebug("Error decrypting Web link %s, %s" % (index, detail))
            self.setWait(4)
            self.wait()
        return package_links

    def _getCipherParams(self, cnl2_form):
        # Get jk
        jk_re = self.CNL2_FORMINPUT_REGEX % self.CNL2_JK_KEY
        vjk = re.findall(jk_re, cnl2_form, re.IGNORECASE)

        # Get crypted
        crypted_re = self.CNL2_FORMINPUT_REGEX % RelinkUs.CNL2_CRYPTED_KEY
        vcrypted = re.findall(crypted_re, cnl2_form, re.IGNORECASE)

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
