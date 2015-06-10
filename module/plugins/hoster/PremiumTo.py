# -*- coding: utf-8 -*-

from __future__ import with_statement

import os

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import fs_encode


class PremiumTo(MultiHoster):
    __name__    = "PremiumTo"
    __type__    = "hoster"
    __version__ = "0.24"

    __pattern__ = r'^unmatchable$'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Premium.to multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CHECK_TRAFFIC = True


    def handlePremium(self, pyfile):
        #raise timeout to 2min
        self.download("http://premium.to/api/getfile.php",
                      get={'username': self.account.username,
                           'password': self.account.password,
                           'link'    : pyfile.url},
                      disposition=True)


    def checkFile(self):
        if self.checkDownload({'nopremium': "No premium account available"}):
            self.retry(60, 5 * 60, "No premium account available")

        err = ''
        if self.req.http.code == '420':
            # Custom error code send - fail
            file = fs_encode(self.lastDownload)
            with open(file, "rb") as f:
                err = f.read(256).strip()
            os.remove(file)

        if err:
            self.fail(err)

        return super(PremiumTo, self).checkFile()


getInfo = create_getInfo(PremiumTo)
