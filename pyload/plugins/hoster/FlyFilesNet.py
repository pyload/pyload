# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.SimpleHoster import SimpleHoster


class FlyFilesNet(SimpleHoster):
    __name    = "FlyFilesNet"
    __type    = "hoster"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?flyfiles\.net/.*'

    __description = """FlyFiles.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = []

    SESSION_PATTERN = r'flyfiles\.net/(.*)/.*'
    NAME_PATTERN = r'flyfiles\.net/.*/(.*)'


    def process(self, pyfile):
        name = re.search(self.NAME_PATTERN, pyfile.url).group(1)
        pyfile.name = unquote_plus(name)

        session = re.search(self.SESSION_PATTERN, pyfile.url).group(1)

        url = "http://flyfiles.net"

        # get download URL
        parsed_url = getURL(url, post={"getDownLink": session}, cookies=True)
        self.logDebug("Parsed URL: %s" % parsed_url)

        if parsed_url == '#downlink|' or parsed_url == "#downlink|#":
            self.logWarning(_("Could not get the download URL. Please wait 10 minutes"))
            self.wait(10 * 60, True)
            self.retry()

        download_url = parsed_url.replace('#downlink|', '')

        self.download(download_url)
