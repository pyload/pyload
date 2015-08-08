# -*- coding: utf-8 -*-

import binascii
import re

from Crypto.Cipher import AES

from module.plugins.internal.Crypter import Crypter
from module.plugins.captcha.ReCaptcha import ReCaptcha


class NCryptIn(Crypter):
    __name__    = "NCryptIn"
    __type__    = "crypter"
    __version__ = "1.37"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?ncrypt\.in/(?P<TYPE>folder|link|frame)-([^/\?]+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """NCrypt.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("stickell", "l.stickell@yahoo.it")]


    JK_KEY = "jk"
    CRYPTED_KEY = "crypted"

    NAME_PATTERN = r'<meta name="description" content="(?P<N>.+?)"'


    def setup(self):
        self.package = None
        self.cleaned_html = None
        self.links_source_order = ["cnl2", "rsdf", "ccf", "dlc", "web"]
        self.protection_type = None


    def decrypt(self, pyfile):
        #: Init
        self.package = pyfile.package()
        package_links = []
        package_name = self.package.name
        folder_name = self.package.folder

        #: Deal with single links
        if self.is_single_link():
            package_links.extend(self.handle_single_link())

        #: Deal with folders
        else:

            #: Request folder home
            self.html = self.request_folder_home()
            self.cleaned_html = self.remove_html_crap(self.html)
            if not self.is_online():
                self.offline()

            #: Check for folder protection
            if self.is_protected():
                self.html = self.unlock_protection()
                self.cleaned_html = self.remove_html_crap(self.html)
                self.handle_errors()

            #: Prepare package name and folder
            (package_name, folder_name) = self.get_package_info()

            #: Extract package links
            for link_source_type in self.links_source_order:
                package_links.extend(self.handle_link_source(link_source_type))
                if package_links:  #: Use only first source which provides links
                    break
            package_links = set(package_links)

        #: Pack and return links
        if package_links:
            self.packages = [(package_name, package_links, folder_name)]


    def is_single_link(self):
        link_type = re.match(self.__pattern__, self.pyfile.url).group('TYPE')
        return link_type in ("link", "frame")


    def request_folder_home(self):
        return self.load(self.pyfile.url)


    def remove_html_crap(self, content):
        patterns = (r'(type="hidden".*?(name=".*?")?.*?value=".*?")',
                    r'display:none;">(.*?)</(div|span)>',
                    r'<div\s+class="jdownloader"(.*?)</div>',
                    r'<table class="global">(.*?)</table>',
                    r'<iframe\s+style="display:none(.*?)</iframe>')
        for pattern in patterns:
            rexpr = re.compile(pattern, re.S)
            content = re.sub(rexpr, "", content)
        return content


    def is_online(self):
        if "Your folder does not exist" in self.cleaned_html:
            self.log_debug("File not m")
            return False
        return True


    def is_protected(self):
        form = re.search(r'<form.*?name.*?protected.*?>(.*?)</form>', self.cleaned_html, re.S)
        if form:
            content = form.group(1)
            for keyword in ("password", "captcha"):
                if keyword in content:
                    self.protection_type = keyword
                    self.log_debug("Links are %s protected" % self.protection_type)
                    return True
        return False


    def get_package_info(self):
        m = re.search(self.NAME_PATTERN, self.html)
        if m:
            name = folder = m.group('N').strip()
            self.log_debug("Found name [%s] and folder [%s] in package info" % (name, folder))
        else:
            name = self.package.name
            folder = self.package.folder
            self.log_debug("Package info not m, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))
        return name, folder


    def unlock_protection(self):
        postData = {}

        form = re.search(r'<form name="protected"(.*?)</form>', self.cleaned_html, re.S).group(1)

        #: Submit package password
        if "password" in form:
            password = self.get_password()
            self.log_debug("Submitting password [%s] for protected links" % password)
            postData['password'] = password

        #: Resolve anicaptcha
        if "anicaptcha" in form:
            self.log_debug("Captcha protected")
            captchaUri = re.search(r'src="(/temp/anicaptcha/.+?)"', form).group(1)
            captcha = self.captcha.decrypt("http://ncrypt.in" + captchaUri)
            self.log_debug("Captcha resolved [%s]" % captcha)
            postData['captcha'] = captcha

        #: Resolve recaptcha
        if "recaptcha" in form:
            self.log_debug("ReCaptcha protected")
            captcha_key = re.search(r'\?k=(.*?)"', form).group(1)
            self.log_debug("Resolving ReCaptcha with key [%s]" % captcha_key)
            recaptcha = ReCaptcha(self)
            response, challenge = recaptcha.challenge(captcha_key)
            postData['recaptcha_challenge_field'] = challenge
            postData['recaptcha_response_field']  = response

        #: Resolve circlecaptcha
        if "circlecaptcha" in form:
            self.log_debug("CircleCaptcha protected")
            captcha_img_url = "http://ncrypt.in/classes/captcha/circlecaptcha.php"
            coords = self.captcha.decrypt(captcha_img_url, input_type="png", output_type='positional', ocr="CircleCaptcha")
            self.log_debug("Captcha resolved, coords [%s]" % str(coords))
            postData['circle.x'] = coords[0]
            postData['circle.y'] = coords[1]

        #: Unlock protection
        postData['submit_protected'] = 'Continue to folder'
        return self.load(self.pyfile.url, post=postData)


    def handle_errors(self):
        if self.protection_type == "password":
            if "This password is invalid!" in self.cleaned_html:
                self.log_debug("Incorrect password, please set right password on 'Edit package' form and retry")
                self.fail(_("Incorrect password, please set right password on 'Edit package' form and retry"))

        if self.protection_type == "captcha":
            if "The securitycheck was wrong!" in self.cleaned_html:
                self.captcha.invalid()
                self.retry()
            else:
                self.captcha.correct()


    def handle_link_source(self, link_source_type):
        #: Check for JS engine
        require_js_engine = link_source_type in ("cnl2", "rsdf", "ccf", "dlc")
        if require_js_engine and not self.js:
            self.log_debug("No JS engine available, skip %s links" % link_source_type)
            return []

        #: Select suitable handler
        if link_source_type == "single":
            return self.handle_single_link()
        if link_source_type == "cnl2":
            return self.handle_CNL2()
        elif link_source_type in ("rsdf", "ccf", "dlc"):
            return self.handle_container(link_source_type)
        elif link_source_type == "web":
            return self.handle_web_links()
        else:
            self.error(_('Unknown source type "%s"') % link_source_type)


    def handle_single_link(self):
        self.log_debug("Handling Single link")
        package_links = []

        #: Decrypt single link
        decrypted_link = self.decrypt_link(self.pyfile.url)
        if decrypted_link:
            package_links.append(decrypted_link)

        return package_links


    def handle_CNL2(self):
        self.log_debug("Handling CNL2 links")
        package_links = []

        if 'cnl2_output' in self.cleaned_html:
            try:
                (vcrypted, vjk) = self._get_cipher_params()
                for (crypted, jk) in zip(vcrypted, vjk):
                    package_links.extend(self._get_links(crypted, jk))
            except Exception:
                self.fail(_("Unable to decrypt CNL2 links"))

        return package_links


    def handle_containers(self):
        self.log_debug("Handling Container links")
        package_links = []

        pattern = r'/container/(rsdf|dlc|ccf)/(\w+)'
        containersLinks = re.findall(pattern, self.html)
        self.log_debug("Decrypting %d Container links" % len(containersLinks))
        for containerLink in containersLinks:
            link = "http://ncrypt.in/container/%s/%s.%s" % (containerLink[0], containerLink[1], containerLink[0])
            package_links.append(link)

        return package_links


    def handle_web_links(self):
        self.log_debug("Handling Web links")
        pattern = r'(http://ncrypt\.in/link-.*?=)'
        links = re.findall(pattern, self.html)

        package_links = []
        self.log_debug("Decrypting %d Web links" % len(links))
        for i, link in enumerate(links):
            self.log_debug("Decrypting Web link %d, %s" % (i + 1, link))
            decrypted_link = self.decrypt(link)
            if decrypted_link:
                package_links.append(decrypted_link)

        return package_links


    def decrypt_link(self, link):
        try:
            url = link.replace("link-", "frame-")
            link = self.load(url, just_header=True)['location']
            return link
        except Exception, detail:
            self.log_debug("Error decrypting link %s, %s" % (link, detail))


    def _get_cipher_params(self):
        pattern = r'<input.*?name="%s".*?value="(.*?)"'

        #: Get jk
        jk_re = pattern % NCryptIn.JK_KEY
        vjk = re.findall(jk_re, self.html)

        #: Get crypted
        crypted_re = pattern % NCryptIn.CRYPTED_KEY
        vcrypted = re.findall(crypted_re, self.html)

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
        self.log_debug("Block has %d links" % len(links))
        return links
