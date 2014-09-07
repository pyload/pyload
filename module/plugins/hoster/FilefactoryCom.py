# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo


def getInfo(urls):
    for url in urls:
        h = getURL(url, just_header=True)
        m = re.search(r'Location: (.+)\r\n', h)
        if m and not re.match(m.group(1), FilefactoryCom.__pattern__):  # It's a direct link! Skipping
            yield (url, 0, 3, url)
        else:  # It's a standard html page
            file_info = parseFileInfo(FilefactoryCom, url, getURL(url))
            yield file_info


class FilefactoryCom(SimpleHoster):
    __name__ = "FilefactoryCom"
    __type__ = "hoster"
    __version__ = "0.50"

    __pattern__ = r'https?://(?:www\.)?filefactory\.com/file/(?P<id>[a-zA-Z0-9]+)'

    __description__ = """Filefactory.com hoster plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    FILE_INFO_PATTERN = r'<div id="file_name"[^>]*>\s*<h2>(?P<N>[^<]+)</h2>\s*<div id="file_info">\s*(?P<S>[\d.]+) (?P<U>\w+) uploaded'
    LINK_PATTERN = r'<a href="(https?://[^"]+)"[^>]*><i[^>]*></i> Download with FileFactory Premium</a>'
    OFFLINE_PATTERN = r'<h2>File Removed</h2>|This file is no longer available'
    PREMIUM_ONLY_PATTERN = r'>Premium Account Required<'

    SH_COOKIES = [(".filefactory.com", "locale", "en_US.utf8")]


    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)
        if "Currently only Premium Members can download files larger than" in self.html:
            self.fail("File too large for free download")
        elif "All free download slots on this server are currently in use" in self.html:
            self.retry(50, 15 * 60, "All free slots are busy")

        m = re.search(r'data-href(?:-direct)?="(http://[^"]+)"', self.html)
        if m:
            t = re.search(r'<div id="countdown_clock" data-delay="(\d+)">', self.html)
            if t:
                t = t.group(1)
            else:
                self.logDebug("Unable to detect countdown duration. Guessing 60 seconds")
                t = 60
            self.wait(t)
            direct = m.group(1)
        else:  # This section could be completely useless now
            # Load the page that contains the direct link
            url = re.search(r"document\.location\.host \+\s*'(.+)';", self.html)
            if url is None:
                self.parseError('Unable to detect free link')
            url = 'http://www.filefactory.com' + url.group(1)
            self.html = self.load(url, decode=True)

            # Free downloads wait time
            waittime = re.search(r'id="startWait" value="(\d+)"', self.html)
            if not waittime:
                self.parseError('Unable to detect wait time')
            self.wait(int(waittime.group(1)))

            # Parse the direct link and download it
            direct = re.search(r'data-href(?:-direct)?="(.*)" class="button', self.html)
            if not direct:
                self.parseError('Unable to detect free direct link')
            direct = direct.group(1)

        self.logDebug('DIRECT LINK: ' + direct)
        self.download(direct, disposition=True)

        check = self.checkDownload({"multiple": "You are currently downloading too many files at once.",
                                    "error": '<div id="errorMessage">'})

        if check == "multiple":
            self.logDebug("Parallel downloads detected; waiting 15 minutes")
            self.retry(wait_time=15 * 60, reason="Parallel downloads")
        elif check == "error":
            self.fail("Unknown error")

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header=True)
        if 'location' in header:
            url = header['location'].strip()
            if not url.startswith("http://"):
                url = "http://www.filefactory.com" + url
        elif 'content-disposition' in header:
            url = self.pyfile.url
        else:
            self.logInfo('You could enable "Direct Downloads" on http://filefactory.com/account/')
            html = self.load(self.pyfile.url)
            m = re.search(self.LINK_PATTERN, html)
            if m:
                url = m.group(1)
            else:
                self.parseError('Unable to detect premium direct link')

        self.logDebug('DIRECT PREMIUM LINK: ' + url)
        self.download(url, disposition=True)
