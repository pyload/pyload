# -*- coding: utf-8 -*-

import re

from time import sleep

from module.plugins.Crypter import Crypter


class DDLMusicOrg(Crypter):
    __name__ = "DDLMusicOrg"
    __type__ = "crypter"
    __version__ = "0.3"

    __pattern__ = r'http://(?:www\.)?ddl-music\.org/captcha/ddlm_cr\d\.php\?\d+\?\d+'

    __description__ = """Ddl-music.org decrypter plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def setup(self):
        self.multiDL = False

    def decrypt(self, pyfile):
        html = self.req.load(pyfile.url, cookies=True)

        if re.search(r"Wer dies nicht rechnen kann", html) is not None:
            self.offline()

        math = re.search(r"(\d+) ([\+-]) (\d+) =\s+<inp", self.html)
        id = re.search(r"name=\"id\" value=\"(\d+)\"", self.html).group(1)
        linknr = re.search(r"name=\"linknr\" value=\"(\d+)\"", self.html).group(1)

        solve = ""
        if math.group(2) == "+":
            solve = int(math.group(1)) + int(math.group(3))
        else:
            solve = int(math.group(1)) - int(math.group(3))
        sleep(3)
        htmlwithlink = self.req.load(pyfile.url, cookies=True,
                                     post={"calc%s" % linknr: solve, "send%s" % linknr: "Send", "id": id,
                                           "linknr": linknr})
        m = re.search(r"<form id=\"ff\" action=\"(.*?)\" method=\"post\">", htmlwithlink)
        if m:
            self.urls = [m.group(1)]
        else:
            self.retry()
