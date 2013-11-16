#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class RgHostNet(SimpleHoster):
    __name__ = "RgHostNet"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?rghost\.net/\d+(?:r=\d+)?"
    __version__ = "0.01"
    __description__ = """RgHost.net Download Hoster"""
    __author_name__ = ("z00nx")
    __author_mail__ = ("z00nx0@gmail.com")

    FILE_INFO_PATTERN = r'<h1>\s+(<a[^>]+>)?(?P<N>[^<]+)(</a>)?\s+<small[^>]+>\s+\((?P<S>[^)]+)\)\s+</small>\s+</h1>'
    FILE_OFFLINE_PATTERN = r'File is deleted|this page is not found'
    DOWNLOAD_LINK_PATTERN = '''<a\s+href="([^"]+)"\s+class="btn\s+large\s+download"[^>]+>Download</a>'''

    def handleFree(self):
        found = re.search(self.DOWNLOAD_LINK_PATTERN, self.html)
        if not found:
            self.parseError("Unable to detect the direct link")
        download_link = found.group(1)
        self.download(download_link, disposition=True)

getInfo = create_getInfo(RgHostNet)
