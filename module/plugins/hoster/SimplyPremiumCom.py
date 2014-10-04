# -*- coding: utf-8 -*-

import re

from datetime import datetime, timedelta

from module.plugins.Hoster import Hoster
from module.plugins.hoster.UnrestrictLi import secondsToMidnight


class SimplyPremiumCom(Hoster):
    __name__ = "SimplyPremiumCom"
    __type__ = "hoster"
    __version__ = "0.03"

    __pattern__ = r'https?://.*(simply-premium)\.com'

    __description__ = """Simply-Premium.com hoster plugin"""
    __author_name__ = "EvolutionClip"
    __author_mail__ = "evolutionclip@live.de"


    def setup(self):
        self.chunkLimit = 16
        self.resumeDownload = False

    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Simply-Premium.com")
            self.fail("No Simply-Premium.com account provided")
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            for i in xrange(5):
                page = self.load('http://www.simply-premium.com/premium.php?info&link=' + pyfile.url)
                self.logDebug("JSON data: " + page)
                if page != '':
                    break
            else:
                self.logInfo("Unable to get API data, waiting 1 minute and retry")
                self.retry(5, 60, "Unable to get API data")

            if '<valid>0</valid>' in page or (
                    "You are not allowed to download from this host" in page and self.premium):
                self.account.relogin(self.user)
                self.retry()
            elif "NOTFOUND" in page:
                self.offline()
            elif "downloadlimit" in page:
                self.logWarning("Reached maximum connctions")
                self.retry(5, 60, "Reached maximum connctions")
            elif "trafficlimit" in page:
                self.logWarning("Reached daily limit for this host")
                self.retry(1, secondsToMidnight(gmt=2), "Daily limit for this host reached")
            elif "hostererror" in page:
                self.logWarning("Hoster temporarily unavailable, waiting 1 minute and retry")
                self.retry(5, 60, "Hoster is temporarily unavailable")
            #page = json_loads(page)
            #new_url = page.keys()[0]
            #self.api_data = page[new_url]

            try:
                self.pyfile.name = re.search(r'<name>([^<]+)</name>', page).group(1)
            except AttributeError:
                self.pyfile.name = ""

            try:
                self.pyfile.size = re.search(r'<size>(\d+)</size>', page).group(1)
            except AttributeError:
                self.pyfile.size = 0

            try:
                new_url = re.search(r'<download>([^<]+)</download>', page).group(1)
            except AttributeError:
                new_url = 'http://www.simply-premium.com/premium.php?link=' + pyfile.url

        if new_url != pyfile.url:
            self.logDebug("New URL: " + new_url)

        self.download(new_url, disposition=True)
