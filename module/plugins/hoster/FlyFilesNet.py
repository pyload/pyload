# -*- coding: utf-8 -*-

import re
import urllib

from ..internal.SimpleHoster import SimpleHoster


class FlyFilesNet(SimpleHoster):
    __name__ = "FlyFilesNet"
    __type__ = "hoster"
    __version__ = "0.15"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?flyfiles\.net/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """FlyFiles.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = []

    SESSION_PATTERN = r'flyfiles\.net/(.*)/.*'
    NAME_PATTERN = r'flyfiles\.net/.*/(.*)'

    def process(self, pyfile):
        name = re.search(self.NAME_PATTERN, pyfile.url).group(1)
        pyfile.name = urllib.unquote_plus(name)

        session = re.search(self.SESSION_PATTERN, pyfile.url).group(1)

        url = "http://flyfiles.net"

        #: Get download URL
        parsed_url = self.load(url, post={'getDownLink': session})
        self.log_debug("Parsed URL: %s" % parsed_url)

        if parsed_url == "#downlink|" or parsed_url == "#downlink|#":
            self.log_warning(
                _("Could not get the download URL. Please wait 10 minutes"))
            self.wait(10 * 60, True)
            self.retry()

        self.link = parsed_url.replace('#downlink|', '')
