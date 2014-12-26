# -*- coding: utf-8 -*-

import re

from datetime import datetime, timedelta

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


def secondsToMidnight(gmt=0):
    now = datetime.utcnow() + timedelta(hours=gmt)

    if now.hour is 0 and now.minute < 10:
        midnight = now
    else:
        midnight = now + timedelta(days=1)

    td = midnight.replace(hour=0, minute=10, second=0, microsecond=0) - now

    if hasattr(td, 'total_seconds'):
        res = td.total_seconds()
    else:  #@NOTE: work-around for python 2.5 and 2.6 missing timedelta.total_seconds
        res = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    return int(res)


class UnrestrictLi(MultiHoster):
    __name__    = "UnrestrictLi"
    __type__    = "hoster"
    __version__ = "0.18"

    __pattern__ = r'https?://(?:[^/]*\.)?(unrestrict|unr)\.li'

    __description__ = """Unrestrict.li hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LOGIN_ACCOUNT = False


    def setup(self):
        self.chunkLimit     = 16
        self.resumeDownload = True


    def handleFree(self):
        for _i in xrange(5):
            page = self.load('https://unrestrict.li/unrestrict.php',
                             post={'link': self.pyfile.url, 'domain': 'long'})
            self.logDebug("JSON data: " + page)
            if page != '':
                break
        else:
            self.logInfo(_("Unable to get API data, waiting 1 minute and retry"))
            self.retry(5, 60, "Unable to get API data")

        if 'Expired session' in page or ("You are not allowed to "
                                         "download from this host" in page and self.premium):
            self.account.relogin(self.user)
            self.retry()

        elif "File offline" in page:
            self.offline()

        elif "You are not allowed to download from this host" in page:
            self.fail(_("You are not allowed to download from this host"))

        elif "You have reached your daily limit for this host" in page:
            self.logWarning(_("Reached daily limit for this host"))
            self.retry(5, secondsToMidnight(gmt=2), "Daily limit for this host reached")

        elif "ERROR_HOSTER_TEMPORARILY_UNAVAILABLE" in page:
            self.logInfo(_("Hoster temporarily unavailable, waiting 1 minute and retry"))
            self.retry(5, 60, "Hoster is temporarily unavailable")

        page = json_loads(page)
        self.link = page.keys()[0]
        self.api_data = page[self.link]

        if self.link != self.pyfile.url:
            self.logDebug("New URL: " + self.link)

        if hasattr(self, 'api_data'):
            self.setNameSize()


    def checkFile(self):
        super(UnrestrictLi, self).checkFile()

        if self.getConfig("history"):
            self.load("https://unrestrict.li/history/", get={'delete': "all"})
            self.logInfo(_("Download history deleted"))


    def setNameSize(self):
        if 'name' in self.api_data:
            self.pyfile.name = self.api_data['name']
        if 'size' in self.api_data:
            self.pyfile.size = self.api_data['size']


getInfo = create_getInfo(UnrestrictLi)
