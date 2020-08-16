# -*- coding: utf-8 -*-

import re

from ..base.simple_decrypter import SimpleDecrypter


class TnyCz(SimpleDecrypter):
    __name__ = "TnyCz"
    __type__ = "decrypter"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?tny\.cz/\w+"
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

    __description__ = """Tny.cz decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r"<title>(?P<N>.+?) - .+</title>"

    def get_links(self):
        m = re.search(r'<a id=\'save_paste\' href="(.+save\.php\?hash=.+)">', self.data)
        return re.findall(".+", self.load(m.group(1))) if m else None
