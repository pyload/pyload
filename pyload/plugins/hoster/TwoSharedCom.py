#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
import re

class TwoSharedCom(SimpleHoster):
    __name__ = "TwoSharedCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?2shared.com/(account/)?(download|get|file|document|photo|video|audio)/.*"
    __version__ = "0.11"
    __description__ = """2Shared Download Hoster"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<h1>(?P<N>.*)</h1>'
    FILE_SIZE_PATTERN = r'<span class="dtitle">File size:</span>\s*(?P<S>[0-9,.]+) (?P<U>[kKMG])i?B'
    FILE_OFFLINE_PATTERN = r'The file link that you requested is not valid\.|This file was deleted\.'
    DOWNLOAD_URL_PATTERN = r"window.location ='([^']+)';"
    
    def setup(self):
        self.resumeDownload = self.multiDL = True

    def handleFree(self):               
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: self.parseError('Download link')
        link = found.group(1)
        self.logDebug("Download URL %s" % link)
        
        self.download(link)

getInfo = create_getInfo(TwoSharedCom)
            