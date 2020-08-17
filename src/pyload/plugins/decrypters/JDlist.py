# -*- coding: utf-8 -*-

import base64

from ..base.decrypter import BaseDecrypter


class JDlist(BaseDecrypter):
    __name__ = "JDlist"
    __type__ = "decrypter"
    __version__ = "0.05"
    __status__ = "testing"

    __pattern__ = r"jdlist://(?P<LIST>[\w\+^_]+==)"
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

    __description__ = """JDlist decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def decrypt(self, pyfile):
        self.links.extend(base64.b64decode(self.info["pattern"]["LIST"]).split(","))
