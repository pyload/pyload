# -*- coding: utf-8 -*-
import re
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class FilezyNet(XFileSharingPro):
    __name__ = "FilezyNet"
    __type__ = "hoster"
    __version__ = "0.1"
    __pattern__ = r"http://filezy.net/.*/.*.html"
    __description__ = """filezy.net hoster plugin"""

    HOSTER_NAME = "filezy.net"

    FILE_SIZE_PATTERN = r'<span class="plansize">(?P<S>[0-9.]+) (?P<U>[kKMG])i?B</span>'
    WAIT_PATTERN = r'<div id="countdown_str" class="seconds">\n<!--Wait--> <span id=".*?">(\d+)</span>'
    DOWNLOAD_JS_PATTERN = r"<script type='text/javascript'>eval(.*)"

    def setup(self):
        self.resumeDownload = True
        self.multiDL = self.premium

    def getDownloadLink(self):
        self.logDebug("Getting download link")

        data = self.getPostParameters()
        self.html = self.load(self.pyfile.url, post = data, ref = True, decode = True)

        obfuscated_js = re.search(self.DOWNLOAD_JS_PATTERN, self.html)
        dl_file_now = self.js.eval(obfuscated_js.group(1))
        link = re.search(self.DIRECT_LINK_PATTERN, dl_file_now)
        return link.group(1)

getInfo = create_getInfo(FilezyNet)
