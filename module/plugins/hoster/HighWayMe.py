# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.plugins.internal.SimpleHoster import secondsToMidnight


class HighWayMe(MultiHoster):
    __name__    = "HighWayMe"
    __type__    = "hoster"
    __version__ = "0.09"

    __pattern__ = r'https?://.+high-way\.my'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """High-Way.me multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def setup(self):
        self.chunkLimit = 4


    def checkErrors(self):
        if '<valid>0</valid>' in self.html:  #@NOTE: This is not working. It should by if 302 Moved Temporarily then ... But I don't now how to implement it.
            self.account.relogin(self.user)
            self.retry()

        elif "<code>9</code>" in self.html:
            self.offline()

        elif "downloadlimit" in self.html:
            self.logWarning(_("Reached maximum connctions"))
            self.retry(5, 60, _("Reached maximum connctions"))

        elif "trafficlimit" in self.html:
            self.logWarning(_("Reached daily limit"))
            self.retry(wait_time=secondsToMidnight(gmt=2), reason="Daily limit for this host reached")

        elif "<code>8</code>" in self.html:
            self.logWarning(_("Hoster temporarily unavailable, waiting 1 minute and retry"))
            self.retry(5, 60, _("Hoster is temporarily unavailable"))


    def handlePremium(self, pyfile):
        for _i in xrange(5):
            self.html = self.load("https://high-way.me/load.php",
                                  get={'link': self.pyfile.url})

            if self.html:
                self.logDebug("JSON data: " + self.html)
                break
        else:
            self.logInfo(_("Unable to get API data, waiting 1 minute and retry"))
            self.retry(5, 60, _("Unable to get API data"))

        self.checkErrors()

        try:
            self.pyfile.name = re.search(r'<name>([^<]+)</name>', self.html).group(1)

        except AttributeError:
            self.pyfile.name = ""

        try:
            self.pyfile.size = re.search(r'<size>(\d+)</size>', self.html).group(1)

        except AttributeError:
            self.pyfile.size = 0

        self.link = re.search(r'<download>([^<]+)</download>', self.html).group(1)


getInfo = create_getInfo(HighWayMe)
