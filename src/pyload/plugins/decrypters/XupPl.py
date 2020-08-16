# -*- coding: utf-8 -*-


from ..base.decrypter import BaseDecrypter


class XupPl(BaseDecrypter):
    __name__ = "XupPl"
    __type__ = "decrypter"
    __version__ = "0.16"
    __status__ = "testing"

    __pattern__ = r"https?://(?:[^/]*\.)?xup\.pl/.+"
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

    __description__ = """Xup.pl decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]

    def decrypt(self, pyfile):
        header = self.load(pyfile.url, just_header=True)
        if "location" in header:
            self.links = [header.get("location")]
        else:
            self.fail(self._("Unable to find link"))
