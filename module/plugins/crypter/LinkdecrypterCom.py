# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiCrypter import MultiCrypter


class LinkdecrypterCom(MultiCrypter):
    __name__    = "LinkdecrypterCom"
    __type__    = "crypter"
    __version__ = "0.32"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Linkdecrypter.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("flowlee", None)]


    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<input type="text" name="password"'
    CAPTCHA_PATTERN  = r'<img class="captcha" src="(.+?)"(.*?)>'
    REDIR_PATTERN    = r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'


    def setup(self):
        self.password = self.get_password()
        self.req.setOption("timeout", 300)


    def decrypt(self, pyfile):
        retries = 5

        post_dict = {'link_cache': "on", 'pro_links': pyfile.url, 'modo_links': "text"}
        self.html = self.load('http://linkdecrypter.com/', post=post_dict)

        while retries:
            m = re.search(self.TEXTAREA_PATTERN, self.html, re.S)
            if m:
                self.urls = [x for x in m.group(1).splitlines() if '[LINK-ERROR]' not in x]

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                captcha_url = 'http://linkdecrypter.com/' + m.group(1)
                result_type = "positional" if "getPos" in m.group(2) else "textual"

                m = re.search(r"<p><i><b>([^<]+)</b></i></p>", self.html)
                msg = m.group(1) if m else ""
                self.log_info(_("Captcha protected link"), result_type, msg)

                captcha = self.captcha.decrypt(captcha_url, output_type=result_type)
                if result_type == "positional":
                    captcha = "%d|%d" % captcha
                self.html = self.load('http://linkdecrypter.com/', post={'captcha': captcha})
                retries -= 1

            elif self.PASSWORD_PATTERN in self.html:
                if self.password:
                    self.log_info(_("Password protected link"))
                    self.html = self.load('http://linkdecrypter.com/', post={'password': self.password})
                else:
                    self.fail(_("Missing password"))

            else:
                retries -= 1
                self.html = self.load('http://linkdecrypter.com/')
