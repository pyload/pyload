# -*- coding: utf-8 -*-

import re
import urlparse

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.SimpleHoster import SimpleHoster, parse_fileInfo


def get_info(urls):
    for url in urls:
        h = get_url(url, just_header=True)
        m = re.search(r'Location: (.+)\r\n', h)
        if m and not re.match(m.group(1), FilefactoryCom.__pattern__):  #: It's a direct link! Skipping
            yield (url, 0, 3, url)
        else:  #: It's a standard html page
            yield parse_fileInfo(FilefactoryCom, url, get_url(url))


class FilefactoryCom(SimpleHoster):
    __name__    = "FilefactoryCom"
    __type__    = "hoster"
    __version__ = "0.57"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?filefactory\.com/(file|trafficshare/\w+)/\w+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Filefactory.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN = r'<div id="file_name"[^>]*>\s*<h2>(?P<N>[^<]+)</h2>\s*<div id="file_info">\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+) uploaded'
    OFFLINE_PATTERN = r'<h2>File Removed</h2>|This file is no longer available|Invalid Download Link'

    LINK_FREE_PATTERN = LINK_PREMIUM_PATTERN = r'"([^"]+filefactory\.com/get.+?)"'

    WAIT_PATTERN = r'<div id="countdown_clock" data-delay="(\d+)">'
    PREMIUM_ONLY_PATTERN = r'>Premium Account Required'

    COOKIES = [("filefactory.com", "locale", "en_US.utf8")]


    def handle_free(self, pyfile):
        if "Currently only Premium Members can download files larger than" in self.html:
            self.fail(_("File too large for free download"))
        elif "All free download slots on this server are currently in use" in self.html:
            self.retry(50, 15 * 60, _("All free slots are busy"))

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))

        self.link = m.group(1)

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(m.group(1))


    def check_file(self):
        check = self.check_download({'multiple': "You are currently downloading too many files at once.",
                                    'error'   : '<div id="errorMessage">'})

        if check == "multiple":
            self.log_debug("Parallel downloads detected; waiting 15 minutes")
            self.retry(wait_time=15 * 60, reason=_("Parallel downloads"))

        elif check == "error":
            self.error(_("Unknown error"))

        return super(FilefactoryCom, self).check_file()


    def handle_premium(self, pyfile):
        self.link = self.direct_link(self.load(pyfile.url, just_header=True))

        if not self.link:
            html = self.load(pyfile.url)
            m = re.search(self.LINK_PREMIUM_PATTERN, html)
            if m:
                self.link = m.group(1)
            else:
                self.error(_("Premium download link not found"))
