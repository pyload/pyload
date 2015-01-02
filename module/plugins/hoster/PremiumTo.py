# -*- coding: utf-8 -*-

from __future__ import with_statement

from os import remove

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import fs_encode


class PremiumTo(MultiHoster):
    __name__    = "PremiumTo"
    __type__    = "hoster"
    __version__ = "0.18"

    __pattern__ = r'^unmatchable$'

    __description__ = """Premium.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def handlePremium(self):
        #raise timeout to 2min
        self.download("http://premium.to/api/getfile.php",
                      get={'username': self.account.username,
                           'password': self.account.password,
                           'link'    : self.pyfile.url},
                      disposition=True)


    def checkFile(self):
        super(PremiumTo, self).checkFile()

        check = self.checkDownload({'nopremium': "No premium account available"})

        if check == "nopremium":
            self.retry(60, 5 * 60, "No premium account available")

        err = ''
        if self.req.http.code == '420':
            # Custom error code send - fail
            lastDownload = fs_encode(self.lastDownload)
            with open(lastDownload, "rb") as f:
                err = f.read(256).strip()
            remove(lastDownload)

        if err:
            self.fail(err)


getInfo = create_getInfo(PremiumTo)
