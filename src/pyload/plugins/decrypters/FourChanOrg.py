# -*- coding: utf-8 -*-

#
# Based on 4chandl by Roland Beermann (https://gist.github.com/enkore/3492599)


import re
import urllib.parse

from ..base.decrypter import BaseDecrypter


class FourChanOrg(BaseDecrypter):
    __name__ = "FourChanOrg"
    __type__ = "decrypter"
    __version__ = "0.38"
    __status__ = "testing"

    __pattern__ = r"http://(?:www\.)?boards\.4chan\.org/\w+/res/(\d+)"
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

    __description__ = """4chan.org folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = []

    def decrypt(self, pyfile):
        pagehtml = self.load(pyfile.url)
        images = set(re.findall(r'(images\.4chan\.org/[^/]*/src/[^"<]+)', pagehtml))
        self.links = [urllib.parse.urljoin("http://", image) for image in images]
