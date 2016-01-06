# -*- coding: utf-8 -*-

import binascii
import re

import Crypto.Cipher

from module.plugins.internal.Crypter import Crypter


class ShareLinksBiz(Crypter):
    __name__    = "ShareLinksBiz"
    __type__    = "crypter"
    __version__ = "1.22"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(share-links|s2l)\.biz/(?P<ID>_?\w+)'
    __config__  = [("activated"         , "bool"          , "Activated"                       , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available", True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"  , "Default")]

    __description__ = """Share-Links.biz decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("Arno-Nymous", None)]


    def setup(self):
        self.base_url = None
        self.file_id = None
        self.package = None


    def decrypt(self, pyfile):
        #: Init
        self.init_file(pyfile)

        #: Request package
        url = self.base_url + '/' + self.file_id
        self.data = self.load(url)

        #: Unblock server (load all images)
        self.unblock_server()

        #: Check for protection
        if self.is_password_protected():
            self.unlock_password_protection()
            self.handle_errors()

        if self.is_captcha_protected():
            self.unlock_captcha_protection()
            self.handle_errors()

        #: Extract package links
        pack_links = []
        pack_links.extend(self.handle_web_links())
        pack_links.extend(self.handle_containers())
        pack_links.extend(self.handle_CNL2())
        pack_links = set(pack_links)

        #: Get package info
        pack_name, pack_folder = self.get_package_info()

        #: Pack
        self.packages = [(pack_name, pack_links, pack_folder)]


    def init_file(self, pyfile):
        url = pyfile.url

        if 's2l.biz' in url:
            header = self.load(url, just_header=True)

            if not 'location' in header:
                self.fail(_("Unable to initialize download"))
            else:
                url = header.get('location')

        if re.match(self.__pattern__, url):
            self.base_url = "http://www.%s.biz" % re.match(self.__pattern__, url).group(1)
            self.file_id = re.match(self.__pattern__, url).group('ID')

        else:
            self.log_debug("Could not initialize, URL [%s] does not match pattern [%s]" % (url, self.__pattern__))
            self.fail(_("Unsupported download link"))

        self.package = pyfile.package()


    def is_online(self):
        if "No usable content was found" in self.data:
            self.log_debug("File not found")
            return False
        else:
            return True


    def is_password_protected(self):
        if re.search(r'<form.*?id="passwordForm".*?>', self.data):
            self.log_debug("Links are protected")
            return True
        return False


    def is_captcha_protected(self):
        if '<map id="captchamap"' in self.data:
            self.log_debug("Links are captcha protected")
            return True
        return False


    def unblock_server(self):
        imgs = re.findall(r'(/template/images/.*?\.gif)', self.data)
        for img in imgs:
            self.load(self.base_url + img)


    def unlock_password_protection(self):
        password = self.get_password()
        self.log_debug("Submitting password [%s] for protected links" % password)
        post = {'password': password, 'login': 'Submit form'}
        url = self.base_url + '/' + self.file_id
        self.data = self.load(url, post=post)


    def unlock_captcha_protection(self):
        #: Get captcha map
        captchaMap = self._get_captcha_map()
        self.log_debug("Captcha map with [%d] positions" % len(captchaMap.keys()))

        #: Request user for captcha coords
        m = re.search(r'<img src="/captcha.gif\?d=(.+?)&PHPSESSID=(.+?)&legend=1"', self.data)
        if m is None:
            self.log_debug("Captcha url data not found, maybe plugin out of date?")
            self.fail(_("Captcha url data not found"))

        captchaUrl = self.base_url + '/captcha.gif?d=%s&PHPSESSID=%s' % (m.group(1), m.group(2))
        self.log_debug("Waiting user for correct position")
        coords = self.captcha.decrypt(captchaUrl, input_type="gif", output_type='positional')
        self.log_debug("Captcha resolved! Coords: {}, {}".format(*coords))

        #: Resolve captcha
        href = self._resolve_coords(coords, captchaMap)
        if href is None:
            self.retry_captcha(wait=5)

        url = self.base_url + href
        self.data = self.load(url)


    def _get_captcha_map(self):
        mapp = {}
        for m in re.finditer(r'<area shape="rect" coords="(.*?)" href="(.*?)"', self.data):
            rect = eval('(' + m.group(1) + ')')
            href = m.group(2)
            mapp[rect] = href
        return mapp


    def _resolve_coords(self, coords, captchaMap):
        x, y = coords
        for rect, href in captchaMap.items():
            x1, y1, x2, y2 = rect
            if (x >= x1 and x <= x2) and (y >= y1 and y <= y2):
                return href


    def handle_errors(self):
        if "The inserted password was wrong" in self.data:
            self.fail(_("Wrong password"))

        if self.captcha:
            if "Your choice was wrong" in self.data:
                self.retry_captcha(wait=5)
            else:
                self.captcha.correct()


    def get_package_info(self):
        name = folder = None

        #: Extract from web package header
        title_re = r'<h2><img.*?/>(.*)</h2>'
        m = re.search(title_re, self.data, re.S)
        if m is not None:
            title = m.group(1).strip()
            if 'unnamed' not in title:
                name = folder = title
                self.log_debug("Found name [%s] and folder [%s] in package info" % (name, folder))

        #: Fallback to defaults
        if not name or not folder:
            name = self.package.name
            folder = self.package.folder
            self.log_debug("Package info not found, defaulting to pyfile name [%s] and folder [%s]" % (name, folder))

        #: Return package info
        return name, folder


    def handle_web_links(self):
        pack_links = []
        self.log_debug("Handling Web links")

        #@TODO: Gather paginated web links
        pattern = r'javascript:_get\(\'(.*?)\', \d+, \'\'\)'
        ids = re.findall(pattern, self.data)
        self.log_debug("Decrypting %d Web links" % len(ids))
        for i, ID in enumerate(ids):
            try:
                self.log_debug("Decrypting Web link %d, [%s]" % (i + 1, ID))

                dwLink = self.base_url + "/get/lnk/" + ID
                res = self.load(dwLink)

                code = re.search(r'frm/(\d+)', res).group(1)
                fwLink = self.base_url + "/get/frm/" + code
                res = self.load(fwLink)

                jscode = re.search(r'<script language="javascript">\s*eval\((.*)\)\s*</script>', res, re.S).group(1)
                jscode = self.js.eval("f = %s" % jscode)
                jslauncher = "window=''; parent={frames:{Main:{location:{href:''}}},location:''}; %s; parent.frames.Main.location.href"

                dlLink = self.js.eval(jslauncher % jscode)

                self.log_debug("JsEngine returns value [%s] for redirection link" % dlLink)

                pack_links.append(dlLink)

            except Exception, detail:
                self.log_debug("Error decrypting Web link [%s], %s" % (ID, detail))

        return pack_links


    def handle_containers(self):
        pack_links = []
        self.log_debug("Handling Container links")

        pattern = r'javascript:_get\(\'(.*?)\', 0, \'(rsdf|ccf|dlc)\'\)'
        containersLinks = re.findall(pattern, self.data)
        self.log_debug("Decrypting %d Container links" % len(containersLinks))
        for containerLink in containersLinks:
            link = "%s/get/%s/%s" % (self.base_url, containerLink[1], containerLink[0])
            pack_links.append(link)
        return pack_links


    def handle_CNL2(self):
        pack_links = []
        self.log_debug("Handling CNL2 links")

        if '/lib/cnl2/ClicknLoad.swf' in self.data:
            try:
                (crypted, jk) = self._get_cipher_params()
                pack_links.extend(self._get_links(crypted, jk))

            except Exception:
                self.fail(_("Unable to decrypt CNL2 links"))

        return pack_links


    def _get_cipher_params(self):
        #: Request CNL2
        code   = re.search(r'ClicknLoad.swf\?code=(.*?)"', self.data).group(1)
        url    = "%s/get/cnl2/%s" % (self.base_url, code)
        res    = self.load(url)
        params = res.split(";;")

        #: Get jk
        strlist = list(params[1].decode('base64'))
        jk      = "".join(strlist[::-1])

        #: Get crypted
        strlist = list(params[2].decode('base64'))
        crypted = "".join(strlist[::-1])

        #: Log and return
        return crypted, jk


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
        self.log_debug("Block has %d links" % len(links))
        return links
