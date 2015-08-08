# -*- coding: utf-8 -*-

from __future__ import with_statement

import binascii
import re
import os

from Crypto.Cipher import AES
from module.plugins.internal.Crypter import Crypter
from module.utils import save_join as fs_join


class RelinkUs(Crypter):
    __name__    = "RelinkUs"
    __type__    = "crypter"
    __version__ = "3.14"
    __status__  = "testing"

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
        #: Init
        self.init_package(pyfile)

        #: Request package
        self.request_package()

        #: Check for online
        if not self.is_online():
            self.offline()

        #: Check for protection
        if self.is_password_protected():
            self.unlock_password_protection()
            self.handle_errors()

        if self.is_captcha_protected():
            self.captcha = True
            self.unlock_captcha_protection()
            self.handle_errors()

        #: Get package name and folder
        (package_name, folder_name) = self.get_package_info()

        #: Extract package links
        package_links = []
        for sources in self.PREFERRED_LINK_SOURCES:
            package_links.extend(self.handle_link_source(sources))
            if package_links:  #: Use only first source which provides links
                break
        package_links = set(package_links)

        #: Pack
        if package_links:
            self.packages = [(package_name, package_links, folder_name)]


    def init_package(self, pyfile):
        self.fileid = re.match(self.__pattern__, pyfile.url).group('ID')
        self.package = pyfile.package()


    def request_package(self):
        self.html = self.load(self.pyfile.url)


    def is_online(self):
        if self.OFFLINE_TOKEN in self.html:
            self.log_debug("File not found")
            return False
        return True


    def is_password_protected(self):
        if self.PASSWORD_TOKEN in self.html:
            self.log_debug("Links are password protected")
            return True


    def is_captcha_protected(self):
        if self.CAPTCHA_TOKEN in self.html:
            self.log_debug("Links are captcha protected")
            return True
        return False


    def unlock_password_protection(self):
        password = self.get_password()

        self.log_debug("Submitting password [%s] for protected links" % password)

        if password:
            passwd_url = self.PASSWORD_SUBMIT_URL + "?id=%s" % self.fileid
            passwd_data = {'id': self.fileid, 'password': password, 'pw': 'submit'}
            self.html = self.load(passwd_url, post=passwd_data)


    def unlock_captcha_protection(self):
        self.log_debug("Request user positional captcha resolving")
        captcha_img_url = self.CAPTCHA_IMG_URL + "?id=%s" % self.fileid
        coords = self.captcha.decrypt(captcha_img_url, input_type="png", output_type='positional', ocr="CircleCaptcha")
        self.log_debug("Captcha resolved, coords [%s]" % str(coords))
        captcha_post_url = self.CAPTCHA_SUBMIT_URL + "?id=%s" % self.fileid
        captcha_post_data = {'button.x': coords[0], 'button.y': coords[1], 'captcha': 'submit'}
        self.html = self.load(captcha_post_url, post=captcha_post_data)


    def get_package_info(self):
        name = folder = None

        #: Try to get info from web
        m = re.search(self.FILE_TITLE_REGEX, self.html)
        if m:
            title = m.group(1).strip()
            if not self.FILE_NOTITLE in title:
                name = folder = title
                self.log_debug("Found name [%s] and folder [%s] in package info" % (name, folder))

        #: Fallback to defaults
        if not name or not folder:
            name = self.package.name
            folder = self.package.folder
            self.log_debug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))

        #: Return package info
        return name, folder


    def handle_errors(self):
        if self.PASSWORD_ERROR_ROKEN in self.html:
            msg = "Incorrect password, please set right password on 'Edit package' form and retry"
            self.log_debug(msg)
            self.fail(_(msg))

        if self.captcha:
            if self.CAPTCHA_ERROR_ROKEN in self.html:
                self.captcha.invalid()
                self.retry()
            else:
                self.captcha.correct()


    def handle_link_source(self, source):
        if source == "cnl2":
            return self.handle_CNL2Links()
        elif source == "dlc":
            return self.handle_DLC_links()
        elif source == "web":
            return self.handle_WEB_links()
        else:
            self.error(_('Unknown source type "%s"') % source)


    def handle_CNL2Links(self):
        self.log_debug("Search for CNL2 links")
        package_links = []
        m = re.search(self.CNL2_FORM_REGEX, self.html, re.S)
        if m:
            cnl2_form = m.group(1)
            try:
                (vcrypted, vjk) = self._get_cipher_params(cnl2_form)
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._get_links(crypted, jk))
            except Exception:
                self.log_debug("Unable to decrypt CNL2 links")
        return package_links


    def handle_DLC_links(self):
        self.log_debug("Search for DLC links")
        package_links = []
        m = re.search(self.DLC_LINK_REGEX, self.html)
        if m:
            container_url = self.DLC_DOWNLOAD_URL + "?id=%s&dlc=1" % self.fileid
            self.log_debug("Downloading DLC container link [%s]" % container_url)
            try:
                dlc = self.load(container_url)
                dlc_filename = self.fileid + ".dlc"
                dlc_filepath = fs_join(self.pyload.config.get("general", "download_folder"), dlc_filename)
                with open(dlc_filepath, "wb") as f:
                    f.write(dlc)
                package_links.append(dlc_filepath)

            except Exception:
                self.fail(_("Unable to download DLC container"))

        return package_links


    def handle_WEB_links(self):
        self.log_debug("Search for WEB links")

        package_links = []
        params        = re.findall(self.WEB_FORWARD_REGEX, self.html)

        self.log_debug("Decrypting %d Web links" % len(params))

        for index, param in enumerate(params):
            try:
                url = self.WEB_FORWARD_URL + "?%s" % param

                self.log_debug("Decrypting Web link %d, %s" % (index + 1, url))

                res  = self.load(url)
                link = re.search(self.WEB_LINK_REGEX, res).group(1)

                package_links.append(link)

            except Exception, detail:
                self.log_debug("Error decrypting Web link %s, %s" % (index, detail))

            self.wait(4)

        return package_links


    def _get_cipher_params(self, cnl2_form):
        #: Get jk
        jk_re = self.CNL2_FORMINPUT_REGEX % self.CNL2_JK_KEY
        vjk = re.findall(jk_re, cnl2_form, re.I)

        #: Get crypted
        crypted_re = self.CNL2_FORMINPUT_REGEX % RelinkUs.CNL2_CRYPTED_KEY
        vcrypted = re.findall(crypted_re, cnl2_form, re.I)

        #: Log and return
        self.log_debug("Detected %d crypted blocks" % len(vcrypted))
        return vcrypted, vjk


    def _get_links(self, crypted, jk):
        #: Get key
        jreturn = self.js.eval("%s f()" % jk)
        self.log_debug("JsEngine returns value [%s]" % jreturn)
        key = binascii.unhexlify(jreturn)

        #: Decrypt
        Key = key
        IV = key
        obj = AES.new(Key, AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        #: Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        #: Log and return
        self.log_debug("Package has %d links" % len(links))
        return links
