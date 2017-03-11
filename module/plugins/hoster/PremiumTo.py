# -*- coding: utf-8 -*-

from __future__ import with_statement

from ..internal.misc import encode
from ..internal.MultiHoster import MultiHoster


class PremiumTo(MultiHoster):
    __name__ = "PremiumTo"
    __type__ = "hoster"
    __version__ = "0.33"
    __status__ = "testing"

    __pattern__ = r'^unmatchable$'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback",
                   "bool",
                   "Fallback to free download if premium fails",
                   False),
                  ("revert_failed", "bool",
                   "Revert to standard download if fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Premium.to multi-hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("RaNaN", "RaNaN@pyload.org"),
                   ("zoidberg", "zoidberg@mujmail.cz"),
                   ("stickell", "l.stickell@yahoo.it"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    CHECK_TRAFFIC = True

    def handle_premium(self, pyfile):
        self.download("http://api.premium.to/api/getfile.php",
                      get={'username': self.account.user,
                           'password': self.account.info['login']['password'],
                           'link': pyfile.url},
                      disposition=True)

    def check_download(self):
        if self.scan_download({'nopremium': "No premium account available"}):
            self.retry(60, 5 * 60, "No premium account available")

        err = ""
        if self.req.http.code == 420:
            #: Custom error code sent - fail
            file = encode(self.last_download)

            with open(file, "rb") as f:
                err = f.read(256).strip()

            self.remove(file)

        if err:
            self.fail(err)

        return MultiHoster.check_download(self)
