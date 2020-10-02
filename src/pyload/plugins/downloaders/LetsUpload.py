# -*- coding: utf-8 -*-

from ..base.simple_downloader import SimpleDownloader
import re
import time


class LetsUpload(SimpleDownloader):
    __name__ = "LetsUpload"
    __type__ = "downloader"
    __version__ = "0.1"
    __status__ = "testing"
    # Note: it does not support Letsupload folders. You must put every file url in the folder on a new line in pyload.

    __pattern__ = r"https?://(?:www\.)?letsupload\.org/.+"
    __config__ = [("enabled", "bool", "Activated", True)]

    __description__ = """Letsupload.org downloader plugin"""
    __license__ = "GPLv3"

    NAME_PATTERN = r'<div class="title"><i class="fa fa-file-text"></i> (?P<N>.+?)</div>'
    SIZE_PATTERN = r"size : <p>(?P<S>[\d.,]+) (?P<U>[\w^_]+)</p>"

    LINK_FREE_PATTERN = r'<a class=\'btn btn-free\' href=\'(?P<url>[^"]+?)\'>'
    LINK_FREE_PATTERN_2 = r'<meta http-equiv="refresh" content="0;url=(?P<url>[^"]+?)" />'

    # Can't simply do "File has been removed" because the text appears at the start of the page for some kind of localization
    OFFLINE_PATTERN = r'<li class="no-side-margin"><i class="fa fa-exclamation-triangle margin-right-20"></i>&nbsp;File has been removed.</li>'
    TEMP_OFFLINE_PATTERN = OFFLINE_PATTERN

    def parse_regex(self, pattern, data, err="Free download link not found"):
        m = re.search(pattern, data)
        if m is None:
            self.error(self._(err))
            return None
        else:
            returnVal = m.group(1)
            return returnVal

    def handle_free(self, pyfile):
        # Get the link to the file that has the real link
        html_file_link = self.parse_regex(self.LINK_FREE_PATTERN, self.data)

        time.sleep(3)  # Sometimes it fails if you request too soon, wait a bit

        # Get the real download link
        html = self.load(html_file_link)
        self.link = self.parse_regex(self.LINK_FREE_PATTERN_2, html)
 
