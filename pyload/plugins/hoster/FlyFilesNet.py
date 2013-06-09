#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.network.RequestFactory import getURL

class FlyFilesNet(SimpleHoster):
    __name__ = "FlyFilesNet"
    __version__ = "0.1"
    __type__ = "hoster"
    __pattern__ = r'http://flyfiles\.net/.*'

    SESSION_PATTERN = r'flyfiles\.net/(.*)/.*'
    FILE_NAME_PATTERN = r'flyfiles\.net/.*/(.*)'

    def process(self, pyfile):

        pyfile.name = re.search(self.FILE_NAME_PATTERN, pyfile.url).group(1)
        pyfile.name = urllib.unquote_plus(pyfile.name)

        session = re.search(self.SESSION_PATTERN, pyfile.url).group(1)

        url = "http://flyfiles.net"

        # get download URL
        parsed_url = getURL(url, post={"getDownLink": session}, cookies=True)
        self.logDebug("Parsed URL: %s" % parsed_url)

        if parsed_url == '#downlink|' or parsed_url == "#downlink|#":
            self.logWarning("Could not get the download URL. Please wait 10 minutes.")
            self.setWait(600, True) # wait 10 minutes
            self.wait()
            self.retry()

        download_url = parsed_url.replace('#downlink|','')

        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)
