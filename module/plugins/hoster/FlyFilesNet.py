# -*- coding: utf-8 -*-

import re

from urllib import unquote

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster


class FlyFilesNet(SimpleHoster):
    __name__    = "FlyFilesNet"
    __type__    = "hoster"
    __version__ = "0.10"

    __pattern__ = r'http://(?:www\.)?flyfiles\.net/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """FlyFiles.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = []

    SESSION_PATTERN = r'flyfiles\.net/(.*)/.*'
    NAME_PATTERN = r'flyfiles\.net/.*/(.*)'


    def process(self, pyfile):
        name = re.search(self.NAME_PATTERN, pyfile.url).group(1)
        pyfile.name = unquote_plus(name)

        session = re.search(self.SESSION_PATTERN, pyfile.url).group(1)

        url = "http://flyfiles.net"

        # get download URL
        parsed_url = getURL(url, post={"getDownLink": session})
        self.logDebug("Parsed URL: %s" % parsed_url)

        if parsed_url == '#downlink|' or parsed_url == "#downlink|#":
            self.logWarning(_("Could not get the download URL. Please wait 10 minutes"))
            self.wait(10 * 60, True)
            self.retry()

        self.link = parsed_url.replace('#downlink|', '')
