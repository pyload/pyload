# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class LinkdecrypterCom(Crypter):
    __name__ = "LinkdecrypterCom"
    __type__ = "crypter"
    __version__ = "0.27"

    __pattern__ = None

    __description__ = """Linkdecrypter.com"""
    __author_name__ = ("zoidberg", "flowlee")
    __author_mail__ = ("zoidberg@mujmail.cz", "")

    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<input type="text" name="password"'
    CAPTCHA_PATTERN = r'<img class="captcha" src="(.+?)"(.*?)>'
    REDIR_PATTERN = r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'


    def decrypt(self, pyfile):

        self.passwords = self.getPassword().splitlines()

        # API not working anymore
        self.urls = self.decryptHTML()
        if not self.urls:
            self.fail('Could not extract any links')

    def decryptAPI(self):

        get_dict = {"t": "link", "url": self.pyfile.url, "lcache": "1"}
        self.html = self.load('http://linkdecrypter.com/api', get=get_dict)
        if self.html.startswith('http://'):
            return self.html.splitlines()

        if self.html == 'INTERRUPTION(PASSWORD)':
            for get_dict['pass'] in self.passwords:
                self.html = self.load('http://linkdecrypter.com/api', get=get_dict)
                if self.html.startswith('http://'):
                    return self.html.splitlines()

        self.logError('API', self.html)
        if self.html == 'INTERRUPTION(PASSWORD)':
            self.fail("No or incorrect password")

        return None

    def decryptHTML(self):

        retries = 5

        post_dict = {"link_cache": "on", "pro_links": self.pyfile.url, "modo_links": "text"}
        self.html = self.load('http://linkdecrypter.com/', post=post_dict, cookies=True, decode=True)

        while self.passwords or retries:
            m = re.search(self.TEXTAREA_PATTERN, self.html, flags=re.DOTALL)
            if m:
                return [x for x in m.group(1).splitlines() if '[LINK-ERROR]' not in x]

            m = re.search(self.CAPTCHA_PATTERN, self.html)
            if m:
                captcha_url = 'http://linkdecrypter.com/' + m.group(1)
                result_type = "positional" if "getPos" in m.group(2) else "textual"

                m = re.search(r"<p><i><b>([^<]+)</b></i></p>", self.html)
                msg = m.group(1) if m else ""
                self.logInfo("Captcha protected link", result_type, msg)

                captcha = self.decryptCaptcha(captcha_url, result_type=result_type)
                if result_type == "positional":
                    captcha = "%d|%d" % captcha
                self.html = self.load('http://linkdecrypter.com/', post={"captcha": captcha}, decode=True)
                retries -= 1

            elif self.PASSWORD_PATTERN in self.html:
                if self.passwords:
                    password = self.passwords.pop(0)
                    self.logInfo("Password protected link, trying " + password)
                    self.html = self.load('http://linkdecrypter.com/', post={'password': password}, decode=True)
                else:
                    self.fail("No or incorrect password")

            else:
                retries -= 1
                self.html = self.load('http://linkdecrypter.com/', cookies=True, decode=True)

        return None
