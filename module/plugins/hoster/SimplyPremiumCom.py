# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster
from module.plugins.internal.misc import seconds_to_midnight


class SimplyPremiumCom(MultiHoster):
    __name__    = "SimplyPremiumCom"
    __type__    = "hoster"
    __version__ = "0.15"
    __status__  = "testing"

    __pattern__ = r'https?://.+simply-premium\.com'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Simply-Premium.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("EvolutionClip", "evolutionclip@live.de")]


    def setup(self):
        self.chunk_limit = 16


    def check_errors(self):
        if '<valid>0</valid>' in self.data or (
                "You are not allowed to download from this host" in self.data and self.premium):
            self.account.relogin()
            self.retry()

        elif "NOTFOUND" in self.data:
            self.offline()

        elif "downloadlimit" in self.data:
            self.log_warning(_("Reached maximum connctions"))
            self.retry(5, 60, _("Reached maximum connctions"))

        elif "trafficlimit" in self.data:
            self.log_warning(_("Reached daily limit for this host"))
            self.retry(wait=seconds_to_midnight(), msg="Daily limit for this host reached")

        elif "hostererror" in self.data:
            self.log_warning(_("Hoster temporarily unavailable, waiting 1 minute and retry"))
            self.retry(5, 60, _("Hoster is temporarily unavailable"))


    def handle_premium(self, pyfile):
        for i in xrange(5):
            self.data = self.load("http://www.simply-premium.com/premium.php", get={'info': "", 'link': self.pyfile.url})

            if self.data:
                self.log_debug("JSON data: " + self.data)
                break
        else:
            self.log_info(_("Unable to get API data, waiting 1 minute and retry"))
            self.retry(5, 60, _("Unable to get API data"))

        self.check_errors()

        try:
            self.pyfile.name = re.search(r'<name>(.+?)</name>', self.data).group(1)

        except AttributeError:
            self.pyfile.name = ""

        try:
            self.pyfile.size = re.search(r'<size>(\d+)</size>', self.data).group(1)

        except AttributeError:
            self.pyfile.size = 0

        try:
            self.link = re.search(r'<download>(.+?)</download>', self.data).group(1)

        except AttributeError:
            self.link = 'http://www.simply-premium.com/premium.php?link=' + self.pyfile.url
