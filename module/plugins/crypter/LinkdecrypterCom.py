# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class LinkdecrypterCom(Crypter):
    __name__    = "LinkdecrypterCom"
    __type__    = "crypter"
    __version__ = "0.29"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Linkdecrypter.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("flowlee", None)]


    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<input type="text" name="password"'
    CAPTCHA_PATTERN  = r'<img class="captcha" src="(.+?)"(.*?)>'
    REDIR_PATTERN    = r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'


    def setup(self):
        self.password = self.getPassword()
        self.req.setOption("timeout", 300)


    def decrypt(self, pyfile):
        retries = 5

        post_dict = {"link_cache": "on", "pro_links": pyfile.url, "modo_links": "text"}
        self.html = self.load('http://linkdecrypter.com/', post=post_dict, cookies=True, decode=True)

        while retries:
            m = re.search(self.TEXTAREA_PATTERN, self.html, flags=re.S)
            if m:
                self.urls = [x for x in m.group(1).splitlines() if '[LINK-ERROR]' not in x]

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                captcha_url = 'http://linkdecrypter.com/' + m.group(1)
                result_type = "positional" if "getPos" in m.group(2) else "textual"

                m = re.search(r"<p><i><b>([^<]+)</b></i></p>", self.html)
                msg = m.group(1) if m else ""
                self.logInfo(_("Captcha protected link"), result_type, msg)

                captcha = self.decryptCaptcha(captcha_url, result_type=result_type)
                if result_type == "positional":
                    captcha = "%d|%d" % captcha
                self.html = self.load('http://linkdecrypter.com/', post={"captcha": captcha}, decode=True)
                retries -= 1

            elif self.PASSWORD_PATTERN in self.html:
                if self.password:
                    self.logInfo(_("Password protected link"))
                    self.html = self.load('http://linkdecrypter.com/', post={'password': self.password}, decode=True)
                else:
                    self.fail(_("Missing password"))

            else:
                retries -= 1
                self.html = self.load('http://linkdecrypter.com/', cookies=True, decode=True)
