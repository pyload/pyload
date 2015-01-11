# -*- coding: utf-8 -*-

import re

from datetime import datetime, timedelta

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.plugins.internal.SimpleHoster import secondsToMidnight


class SimplyPremiumCom(MultiHoster):
    __name__    = "SimplyPremiumCom"
    __type__    = "hoster"
    __version__ = "0.08"

    __pattern__ = r'https?://.+simply-premium\.com'

    __description__ = """Simply-Premium.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def setup(self):
        self.chunkLimit = 16


    def handlePremium(self, pyfile):
        for i in xrange(5):
            page = self.load("http://www.simply-premium.com/premium.php", get={'info': "", 'link': self.pyfile.url})
            self.logDebug("JSON data: " + page)
            if page != '':
                break
        else:
            self.logInfo(_("Unable to get API data, waiting 1 minute and retry"))
            self.retry(5, 60, "Unable to get API data")

        if '<valid>0</valid>' in page or (
                "You are not allowed to download from this host" in page and self.premium):
            self.account.relogin(self.user)
            self.retry()

        elif "NOTFOUND" in page:
            self.offline()

        elif "downloadlimit" in page:
            self.logWarning(_("Reached maximum connctions"))
            self.retry(5, 60, "Reached maximum connctions")

        elif "trafficlimit" in page:
            self.logWarning(_("Reached daily limit for this host"))
            self.retry(wait_time=secondsToMidnight(gmt=2), reason="Daily limit for this host reached")

        elif "hostererror" in page:
            self.logWarning(_("Hoster temporarily unavailable, waiting 1 minute and retry"))
            self.retry(5, 60, "Hoster is temporarily unavailable")

        try:
            self.pyfile.name = re.search(r'<name>([^<]+)</name>', page).group(1)
        except AttributeError:
            self.pyfile.name = ""

        try:
            self.pyfile.size = re.search(r'<size>(\d+)</size>', page).group(1)
        except AttributeError:
            self.pyfile.size = 0

        try:
            self.link = re.search(r'<download>([^<]+)</download>', page).group(1)
        except AttributeError:
            self.link = 'http://www.simply-premium.com/premium.php?link=' + self.pyfile.url

        if self.link != self.pyfile.url:
            self.logDebug("New URL: " + self.link)


getInfo = create_getInfo(SimplyPremiumCom)
