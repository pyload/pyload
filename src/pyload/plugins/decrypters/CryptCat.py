# -*- coding: utf-8 -*-
import re

from ..base.simple_decrypter import SimpleDecrypter


class CryptCat(SimpleDecrypter):
    __name__ = "CryptCat"
    __type__ = "decrypter"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?crypt\.cat/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """crypt.cat decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    OFFLINE_PATTERN = r"Folder not available!"

    LINK_PATTERN = r'<input .+?readonly="" value="\s*(.+?)" type="text">'

    def get_links(self):
        baseurl = self.req.http.last_effective_url
        url, inputs = self.parse_html_form()

        if ">Enter your password.<" in self.data:
            password = self.get_password()
            if not password:
                self.fail(self._("Password required"))

            inputs["Pass1"] = password

        elif "Enter Captcha" in self.data:
            m = re.search(r'<img src="(.+?)"', self.data)
            if m is not None:
                captcha_code = self.captcha.decrypt(m.group(1), input_type="jpeg")
                inputs["security_code"] = captcha_code

            else:
                return []

        else:
            return []

        self.data = self.load(baseurl, post=inputs, ref=baseurl)

        if "You have entered an incorrect password." in self.data:
            self.fail(self._("Wrong password"))

        elif "Your filled the captcha wrongly!" in self.data:
            self.retry_captcha()

        return re.findall(self.LINK_PATTERN, self.data)
