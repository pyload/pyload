# -*- coding: utf-8 -*-

import re
import urllib.parse

from ..base.simple_decrypter import SimpleDecrypter


class DlProtectCom(SimpleDecrypter):
    __name__ = "DlProtectCom"
    __type__ = "decrypter"
    __version__ = "0.13"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?dl-protect1\.com/\w+"
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

    __description__ = """Dl-protect.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def get_links(self):
        if "Cliquez sur continuer pour voir le(s) lien" in self.data:
            self.data = self.load(self.pyfile.url, post={"submit": "Continuer"})

        if 'img src="captcha.php' in self.data:
            captcha_code = self.captcha.decrypt(
                urllib.parse.urljoin(self.pyfile.url, "/captcha.php"), input_type="jpeg"
            )
            self.data = self.load(
                self.pyfile.url, post={"captchaCode": captcha_code, "submit": ""}
            )

            if "Le code de sécurité est incorrect" in self.data:
                self.retry_captcha()

        return re.findall(r'<a href="(?P<id>[^/].+?)">(?P=id)</a>', self.data)
