# -*- coding: utf-8 -*-

import re

from urllib import unquote

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster


class FlyFilesNet(SimpleHoster):
    __name__ = "FlyFilesNet"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?flyfiles\.net/.*'

    __description__ = """FlyFiles.net hoster plugin"""
    __author_name__ = None
    __author_mail__ = None

    SESSION_PATTERN = r'flyfiles\.net/(.*)/.*'
    FILE_NAME_PATTERN = r'flyfiles\.net/.*/(.*)'


    def process(self, pyfile):
        name = re.search(self.FILE_NAME_PATTERN, pyfile.url).group(1)
        pyfile.name = unquote_plus(name)

        session = re.search(self.SESSION_PATTERN, pyfile.url).group(1)

        url = "http://flyfiles.net"

        # get download URL
        parsed_url = getURL(url, post={"getDownLink": session}, cookies=True)
        self.logDebug("Parsed URL: %s" % parsed_url)

        if parsed_url == '#downlink|' or parsed_url == "#downlink|#":
            self.logWarning("Could not get the download URL. Please wait 10 minutes.")
            self.wait(10 * 60, True)
            self.retry()

        download_url = parsed_url.replace('#downlink|', '')

        self.logDebug("Download URL: %s" % download_url)
        self.download(download_url)
