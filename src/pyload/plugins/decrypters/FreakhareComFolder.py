# -*- coding: utf-8 -*-

import re

from ..base.simple_decrypter import SimpleDecrypter


class FreakhareComFolder(SimpleDecrypter):
    __name__ = "FreakhareComFolder"
    __type__ = "decrypter"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?freakshare\.com/folder/.+"
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

    __description__ = """Freakhare.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    LINK_PATTERN = r'<a href="(http://freakshare\.com/files/.+?)" target="_blank">'
    NAME_PATTERN = r"Folder:</b> (?P<N>.+)"
    PAGES_PATTERN = r"Pages: +(\d+)"

    def load_page(self, page_n):
        if not hasattr(self, "f_id") and not hasattr(self, "f_md5"):
            m = re.search(
                r"http://freakshare.com/\?x=folder&f_id=(\d+)&f_md5=(\w+)", self.data
            )
            if m is not None:
                self.f_id = m.group(1)
                self.f_md5 = m.group(2)
        return self.load(
            "http://freakshare.com/",
            get={
                "x": "folder",
                "f_id": self.f_id,
                "f_md5": self.f_md5,
                "entrys": "20",
                "page": page_n - 1,
                "order": "",
            },
        )
