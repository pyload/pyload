# -*- coding: utf-8 -*-
import re

from ..base.multi_decrypter import MultiDecrypter


class LinkdecrypterCom(MultiDecrypter):
    __name__ = "LinkdecrypterCom"
    __type__ = "decrypter"
    __version__ = "0.39"
    __status__ = "testing"

    __pattern__ = r"^unmatchable$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Linkdecrypter.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz"), ("flowlee", None)]

    TEXTAREA_PATTERN = r'<textarea name="links" wrap="off" readonly="1" class="caja_des">(.+)</textarea>'
    PASSWORD_PATTERN = r'<input type="text" name="password"'
    CAPTCHA_PATTERN = r'<img class="captcha" src="(.+?)"(.*?)>'
    REDIR_PATTERN = (
        r'<i>(Click <a href="./">here</a> if your browser does not redirect you).</i>'
    )

    def setup(self):
        self.req.set_option("timeout", 300)

    def decrypt(self, pyfile):
        retries = 5

        post_dict = {"link_cache": "on", "pro_links": pyfile.url, "modo_links": "text"}
        self.data = self.load("http://linkdecrypter.com/", post=post_dict)

        while retries:
            m = re.search(self.TEXTAREA_PATTERN, self.data, re.S)
            if m is not None:
                self.links = [
                    x for x in m.group(1).splitlines() if "[LINK-ERROR]" not in x
                ]

            m = re.search(self.CAPTCHA_PATTERN, self.data)
            if m is not None:
                captcha_url = "http://linkdecrypter.com/" + m.group(1)
                result_type = "positional" if "getPos" in m.group(2) else "textual"

                m = re.search(r"<p><i><b>(.+?)</b></i></p>", self.data)
                msg = m.group(1) if m else ""
                self.log_info(self._("Captcha protected link"), result_type, msg)

                captcha = self.captcha.decrypt(captcha_url, output_type=result_type)
                if result_type == "positional":
                    captcha = "{}|{}".format(*captcha)
                self.data = self.load(
                    "http://linkdecrypter.com/", post={"captcha": captcha}
                )
                retries -= 1

            elif self.PASSWORD_PATTERN in self.data:
                password = self.get_password()
                if password:
                    self.log_info(self._("Password protected link"))
                    self.data = self.load(
                        "http://linkdecrypter.com/", post={"password": password}
                    )
                else:
                    self.fail(self._("Missing password"))

            else:
                retries -= 1
                self.data = self.load("http://linkdecrypter.com/")
