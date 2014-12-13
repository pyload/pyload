# -*- coding: utf-8 -*-

from __future__ import with_statement

from os import remove
from os.path import exists
from urllib import quote

from pyload.plugin.Hoster import Hoster
from pyload.utils import fs_encode


class PremiumTo(Hoster):
    __name    = "PremiumTo"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'https?://(?:www\.)?premium\.to/.+'

    __description = """Premium.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.resumeDownload = True
        self.chunkLimit = 1


    def process(self, pyfile):
        if not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "premium.to")
            self.fail(_("No premium.to account provided"))

        self.logDebug("Old URL: %s" % pyfile.url)

        tra = self.getTraffic()

        #raise timeout to 2min
        self.req.setOption("timeout", 120)

        self.download("http://premium.to/api/getfile.php",
                      get={'username': self.account.username,
                           'password': self.account.password,
                           'link'    : quote(pyfile.url, "")},
                      disposition=True)

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
        self.logInfo(_("Filesize: %d, Traffic used %d, traffic left %d") % (pyfile.size, tra - trb, trb))

        if err:
            self.fail(err)


    def getTraffic(self):
        try:
            api_r = self.load("http://premium.to/api/straffic.php",
                              get={'username': self.account.username, 'password': self.account.password})
            traffic = sum(map(int, api_r.split(';')))
        except Exception:
            traffic = 0
        return traffic
