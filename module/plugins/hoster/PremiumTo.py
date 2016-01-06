# -*- coding: utf-8 -*-

from __future__ import with_statement

import os

from module.plugins.internal.MultiHoster import MultiHoster
from module.plugins.internal.misc import encode


class PremiumTo(MultiHoster):
    __name__    = "PremiumTo"
    __type__    = "hoster"
    __version__ = "0.29"
    __status__  = "testing"

    __pattern__ = r'^unmatchable$'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Premium.to multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CHECK_TRAFFIC = True


    def handle_premium(self, pyfile):
        #: Raise timeout to 2 min
        self.download("http://premium.to/api/getfile.php",
                      get={'username': self.account.username,
                           'password': self.account.password,
                           'link'    : pyfile.url},
                      disposition=True)


    def check_download(self):
        if self.scan_download({'nopremium': "No premium account available"}):
            self.retry(60, 5 * 60, "No premium account available")

        err = ""
        if self.req.http.code == "420":
            #: Custom error code send - fail
            file = encode(self.last_download)

            with open(file, "rb") as f:
                err = f.read(256).strip()

            self.remove(file)

        if err:
            self.fail(err)

        return super(PremiumTo, self).check_download()
