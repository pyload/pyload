# -*- coding: utf-8 -*-

from __future__ import with_statement

import os

from pyload.plugin.internal.MultiHoster import MultiHoster
from pyload.utils import fs_encode


class PremiumTo(MultiHoster):
    __name    = "PremiumTo"
    __type    = "hoster"
    __version = "0.22"

    __pattern = r'^unmatchable$'
    __config  = [("use_premium", "bool", "Use premium account if available", True)]

    __description = """Premium.to multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    CHECK_TRAFFIC = True


    def handle_premium(self, pyfile):
        # raise timeout to 2min
        self.download("http://premium.to/api/getfile.php",
                      get={'username': self.account.username,
                           'password': self.account.password,
                           'link'    : pyfile.url},
                      disposition=True)


    def checkFile(self, rules={}):
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

        return super(PremiumTo, self).checkFile(rules)
