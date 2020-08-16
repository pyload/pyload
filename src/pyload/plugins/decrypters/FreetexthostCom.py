# -*- coding: utf-8 -*-
import re

from ..base.simple_decrypter import SimpleDecrypter


class FreetexthostCom(SimpleDecrypter):
    __name__ = "FreetexthostCom"
    __type__ = "decrypter"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?freetexthost\.com/\w+"
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

    __description__ = """Freetexthost.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    def get_links(self):
        m = re.search(
            r'<div id="contentsinner">\s*(.+)<div class="viewcount">', self.data, re.S
        )
        if m is None:
            self.error(self._("Unable to extract links"))
        links = m.group(1)
        return links.strip().split("<br />\r\n")
