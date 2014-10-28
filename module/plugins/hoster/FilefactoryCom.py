# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo


def getInfo(urls):
    for url in urls:
        h = getURL(url, just_header=True)
        m = re.search(r'Location: (.+)\r\n', h)
        if m and not re.match(m.group(1), FilefactoryCom.__pattern__):  #: It's a direct link! Skipping
            yield (url, 0, 3, url)
        else:  #: It's a standard html page
            file_info = parseFileInfo(FilefactoryCom, url, getURL(url))
            yield file_info


class FilefactoryCom(SimpleHoster):
    __name__    = "FilefactoryCom"
    __type__    = "hoster"
    __version__ = "0.52"

    __pattern__ = r'https?://(?:www\.)?filefactory\.com/(file|trafficshare/\w+)/\w+'

    __description__ = """Filefactory.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_INFO_PATTERN = r'<div id="file_name"[^>]*>\s*<h2>(?P<N>[^<]+)</h2>\s*<div id="file_info">\s*(?P<S>[\d.,]+) (?P<U>[\w^_]+) uploaded'
    OFFLINE_PATTERN = r'<h2>File Removed</h2>|This file is no longer available'

    LINK_PATTERN = r'"([^"]+filefactory\.com/get.+?)"'

    WAIT_PATTERN = r'<div id="countdown_clock" data-delay="(\d+)">'
    PREMIUM_ONLY_PATTERN = r'>Premium Account Required'

    COOKIES = [(".filefactory.com", "locale", "en_US.utf8")]


    def handleFree(self):
        if "Currently only Premium Members can download files larger than" in self.html:
            self.fail(_("File too large for free download"))
        elif "All free download slots on this server are currently in use" in self.html:
            self.retry(50, 15 * 60, _("All free slots are busy"))

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Free download link not found"))

        dl_link = m.group(1)

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.wait(m.group(1))

        self.download(dl_link, disposition=True)

        check = self.checkDownload({'multiple': "You are currently downloading too many files at once.",
                                    'error': '<div id="errorMessage">'})

        if check == "multiple":
            self.logDebug("Parallel downloads detected; waiting 15 minutes")
            self.retry(wait_time=15 * 60, reason=_("Parallel downloads"))
        elif check == "error":
            self.error(_("Unknown error"))


    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)

        if 'location' in header:
            url = header['location'].strip()
            if not url.startswith("http://"):
                url = urljoin("http://www.filefactory.com", url)
        elif 'content-disposition' in header:
            url = self.pyfile.url
        else:
            html = self.load(self.pyfile.url)
            m = re.search(self.LINK_PATTERN, html)
            if m:
                url = m.group(1)
            else:
                self.error(_("Premium download link not found"))

        self.download(url, disposition=True)
