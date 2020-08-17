# -*- coding: utf-8 -*-

import re

from ..base.simple_decrypter import SimpleDecrypter


class HflixIn(SimpleDecrypter):
    __name__ = "HflixIn"
    __type__ = "decrypter"
    __version__ = "0.12"
    __status__ = "testing"

    __pattern__ = r"http://(www\.)?hflix\.in/\w+"

    __description__ = """Hflix.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    def decrypt(self, pyfile):
        headers = self.load(pyfile.url, just_header=True)
        if "refresh" in headers and headers["refresh"]:
            m = re.search(r"\d+;url=(.+)", headers["refresh"])
            if m and "http://hflix.in/admin" not in m.group(1):
                self.packages.append(
                    (pyfile.package().name, [m.group(1)], pyfile.package().name)
                )

            else:
                self.offline()
