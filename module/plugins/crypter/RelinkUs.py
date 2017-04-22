# -*- coding: utf-8 -*-

from __future__ import with_statement

import binascii
import re

import Crypto.Cipher.AES

from ..captcha.SolveMedia import SolveMedia
from ..internal.Captcha import Captcha
from ..internal.Crypter import Crypter
from ..internal.misc import fsjoin, replace_patterns


class RelinkUs(Crypter):
    __name__ = "RelinkUs"
    __type__ = "crypter"
    __version__ = "3.21"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?relink\.(?:us|to)/(f/|((view|go)\.php\?id=))(?P<ID>.+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Relink.us decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                   ("AndroKev", "neureither.kevin@gmail.com")]

    URL_REPLACEMENTS = [(__pattern__ + '.*', r'http://relink.to/f/\g<ID>')]

    PREFERRED_LINK_SOURCES = ["cnl2", "dlc", "web"]

    OFFLINE_TOKEN = r'<title>Tattooside'

    PASSWORD_TOKEN = r'container_password.php'
    PASSWORD_ERROR_ROKEN = r'You have entered an incorrect password'
    PASSWORD_SUBMIT_URL = r'http://relink.to/container_password.php'

    CAPTCHA_TOKEN = r'container_captcha.php'
    CIRCLE_CAPTCHA_PATTERN = r'id="captcha_id" value="(\w+?)"'
    CAPTCHA_ERROR_ROKEN = r'You have solved the captcha wrong'
    CIRCLE_CAPTCHA_IMG_URL = r'http://relink.to/core/captcha/circlecaptcha.php'
    CAPTCHA_SUBMIT_URL = r'http://relink.to/container_captcha.php'

    FILE_TITLE_PATTERN = r'<th>Title</th><td>(.*)</td></tr>'
    FILE_NOTITLE = r'No title'

    CNL2_FORM_PATTERN = r'<form id="cnl_form-(.*?)</form>'
    CNL2_FORMINPUT_PATTERN = r'<input.*?name="%s".*?value="(.*?)"'
    CNL2_JK_KEY = "jk"
    CNL2_CRYPTED_KEY = "crypted"

    DLC_LINK_PATTERN = r'<a href=".*?" class="dlc_button" target="_blank">'
    DLC_DOWNLOAD_URL = r'http://relink.to/download.php'

    WEB_FORWARD_PATTERN = r'getFile\(\'(.+)\'\)'
    WEB_FORWARD_URL = r'http://relink.to/frame.php'
    WEB_LINK_PATTERN = r'<iframe name="Container" height="100%" frameborder="no" width="100%" src="(.+)"></iframe>'

    def setup(self):
        self.file_id = None
        self.package = None
        self.captcha = Captcha(self.pyfile)

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
            self.unlock_captcha_protection()
            self.handle_errors()

        #: Get package name and folder
        pack_name, folder_name = self.get_package_info()

        #: Extract package links
        pack_links = []
        for sources in self.PREFERRED_LINK_SOURCES:
            pack_links.extend(self.handle_link_source(sources))
            if pack_links:  #: Use only first source which provides links
                break
        pack_links = set(pack_links)

        #: Pack
        if pack_links:
            self.packages = [(pack_name, pack_links, folder_name)]

    def init_package(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)
        self.file_id = re.match(self.__pattern__, pyfile.url).group('ID')
        self.package = pyfile.package()

    def request_package(self):
        self.data = self.load(self.pyfile.url)

    def is_online(self):
        if self.OFFLINE_TOKEN in self.data:
            self.log_debug("File not found")
            return False
        return True

    def is_password_protected(self):
        if self.PASSWORD_TOKEN in self.data:
            self.log_debug("Links are password protected")
            return True

    def is_captcha_protected(self):
        if self.CAPTCHA_TOKEN in self.data:
            self.log_debug("Links are captcha protected")
            return True
        return False

    def unlock_password_protection(self):
        password = self.get_password()

        self.log_debug(
            "Submitting password [%s] for protected links" %
            password)

        if password:
            passwd_url = self.PASSWORD_SUBMIT_URL + "?id=%s" % self.file_id
            passwd_data = {
                'id': self.file_id,
                'password': password,
                'pw': 'submit'}
            self.data = self.load(passwd_url, post=passwd_data)

    def unlock_captcha_protection(self):
        m = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.data)
        if m is not None:
            self.log_debug("Request circle captcha resolving")
            captcha_id = m.group(1)

            coords = self.captcha.decrypt(
                self.CIRCLE_CAPTCHA_IMG_URL,
                get={
                    'id': captcha_id},
                input_type="png",
                output_type='positional')  # , ocr="CircleCaptcha")
            self.log_debug(
                "Captcha resolved, coords (%s,%s)" %
                (coords[0], coords[1]))

            post_data = {'button.x': coords[0],
                         'button.y': coords[1],
                         'captcha_id': captcha_id,
                         'captcha_type': "RelinkCircle",
                         'captcha': "submit"}

        else:
            solvemedia = SolveMedia(self.pyfile)
            captcha_key = solvemedia.detect_key()
            if captcha_key:
                self.log_debug("Request SolveMedia captcha resolving")
                response, challenge = solvemedia.challenge()

                post_data = {'adcopy_response': response,
                             'adcopy_challenge': challenge,
                             'captcha_type': "Solvemedia",
                             'submit': "Continue",
                             'captcha': "submit"}

            else:
                self.log_error(_("Unknown captcha type detected"))
                self.fail(_("Unknown captcha type"))

        self.data = self.load(self.CAPTCHA_SUBMIT_URL,
                              ref=False,  # ref=self.CAPTCHA_SUBMIT_URL + "&id=" + self.file_id,
                              get={'id': self.file_id},
                              post=post_data)

    def get_package_info(self):
        name = folder = None

        #: Try to get info from web
        # self.data = self.load(self.pyfile.url)
        m = re.search(self.FILE_TITLE_PATTERN, self.data)
        if m is not None:
            title = m.group(1).strip()
            if not self.FILE_NOTITLE in title:
                name = folder = title
                self.log_debug(
                    "Found name [%s] and folder [%s] in package info" %
                    (name, folder))

        #: Fallback to defaults
        if not name or not folder:
            name = self.package.name
            folder = self.package.folder
            self.log_debug(
                "Package info not found, defaulting to pyfile name [%s] and folder [%s]" %
                (name, folder))

        #: Return package info
        return name, folder

    def handle_errors(self):
        if self.PASSWORD_ERROR_ROKEN in self.data:
            self.fail(_("Wrong password"))

        if self.captcha.task:
            if self.CAPTCHA_ERROR_ROKEN in self.data:
                self.retry_captcha()
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
        pack_links = []
        m = re.search(self.CNL2_FORM_PATTERN, self.data, re.S)
        if m is not None:
            cnl2_form = m.group(1)
            try:
                (vcrypted, vjk) = self._get_cipher_params(cnl2_form)
                for (crypted, jk) in zip(vcrypted, vjk):
                    pack_links.extend(self._get_links(crypted, jk))

            except Exception:
                self.log_debug("Unable to decrypt CNL2 links", trace=True)

        return pack_links

    def handle_DLC_links(self):
        self.log_debug("Search for DLC links")
        pack_links = []
        m = re.search(self.DLC_LINK_PATTERN, self.data)
        if m is not None:
            container_url = self.DLC_DOWNLOAD_URL + "?id=%s&dlc=1" % self.file_id
            self.log_debug(
                "Downloading DLC container link [%s]" % container_url)
            try:
                dlc = self.load(container_url)
                dlc_filename = self.file_id + ".dlc"
                dlc_filepath = fsjoin(
                    self.pyload.config.get(
                        'general',
                        'download_folder'),
                    dlc_filename)
                with open(dlc_filepath, "wb") as f:
                    f.write(dlc)
                pack_links.append(dlc_filepath)

            except Exception:
                self.fail(_("Unable to download DLC container"))

        return pack_links

    def handle_WEB_links(self):
        self.log_debug("Search for WEB links")

        pack_links = []
        params = re.findall(self.WEB_FORWARD_PATTERN, self.data)

        self.log_debug("Decrypting %d Web links" % len(params))

        for index, param in enumerate(params):
            try:
                url = self.WEB_FORWARD_URL + "?%s" % param

                self.log_debug(
                    "Decrypting Web link %d, %s" % (index + 1, url))

                res = self.load(url)
                link = re.search(self.WEB_LINK_PATTERN, res).group(1)

                pack_links.append(link)

            except Exception, detail:
                self.log_debug(
                    "Error decrypting Web link %s, %s" % (index, detail))

            self.wait(4)

        return pack_links

    def _get_cipher_params(self, cnl2_form):
        #: Get jk
        jk_re = self.CNL2_FORMINPUT_PATTERN % self.CNL2_JK_KEY
        vjk = re.findall(jk_re, cnl2_form, re.I)

        #: Get crypted
        crypted_re = self.CNL2_FORMINPUT_PATTERN % RelinkUs.CNL2_CRYPTED_KEY
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
        obj = Crypto.Cipher.AES.new(Key, Crypto.Cipher.AES.MODE_CBC, IV)
        text = obj.decrypt(crypted.decode('base64'))

        #: Extract links
        text = text.replace("\x00", "").replace("\r", "")
        links = filter(bool, text.split('\n'))

        #: Log and return
        self.log_debug("Package has %d links" % len(links))
        return links
