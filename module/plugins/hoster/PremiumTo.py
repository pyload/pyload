# -*- coding: utf-8 -*-

from __future__ import with_statement

from os import remove
from os.path import exists
from urllib import quote

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.utils import fs_encode


class PremiumTo(SimpleHoster):
    __name__    = "PremiumTo"
    __type__    = "hoster"
    __version__ = "0.12"

    __pattern__ = r'https?://(?:www\.)?premium\.to/.*'

    __description__ = """Premium.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    MULTI_HOSTER = True


    def setup(self):
        self.resumeDownload = True
        self.chunkLimit     = 1


    def handleMulti(self):
        tra = self.getTraffic()

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.link = True
        self.download("http://premium.to/api/getfile.php",
                      get={'username': self.account.username,
                           'password': self.account.password,
                           'link'    : quote(self.pyfile.url, "")},
                      disposition=True)


    def checkFile(self):
        check = self.checkDownload({"nopremium": "No premium account available"})

        if check == "nopremium":
            self.retry(60, 5 * 60, "No premium account available")

        err = ''
        if self.req.http.code == '420':
            # Custom error code send - fail
            lastDownload = fs_encode(self.lastDownload)

            if exists(lastDownload):
                with open(lastDownload, "rb") as f:
                    err = f.read(256).strip()
                remove(lastDownload)
            else:
                err = _('File does not exist')

        trb = self.getTraffic()
        self.logInfo(_("Filesize: %d, Traffic used %d, traffic left %d") % (self.pyfile.size, tra - trb, trb))

        if err:
            self.fail(err)


    def getTraffic(self):
        try:
            api_r = self.load("http://premium.to/api/straffic.php",
                              get={'username': self.account.username, 'password': self.account.password})
            traffic = sum(map(int, api_r.split(';')))
        except:
            traffic = 0
        return traffic


getInfo = create_getInfo(PremiumTo)
