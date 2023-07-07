# -*- coding: utf-8 -*

from ..base.decrypter import BaseDecrypter


class WetransferComDereferer(BaseDecrypter):
    __name__ = "WetransferComDereferer"
    __type__ = "decrypter"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"https?://we\.tl/[\-\w]{12}"
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

    __description__ = """we.tl dereferer plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def decrypt(self, pyfile):
        headers = self.load(pyfile.url, just_header=True)
        link = headers.get("location")
        if link is not None:
            self.packages = [(pyfile.package().folder, [link], pyfile.package().name)]
