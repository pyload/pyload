#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
import re

class FourSharedCom(SimpleHoster):
    __name__ = "FourSharedCom"
    __type__ = "hoster"
    __pattern__ = r"http://[\w\.]*?4shared(-china)?\.com/(account/)?(download|get|file|document|photo|video|audio|office)/.+?/.*"
    __version__ = "0.28"
    __description__ = """4Shared Download Hoster"""
    __author_name__ = ("jeix", "zoidberg")
    __author_mail__ = ("jeix@hasnomail.de", "zoidberg@mujmail.cz")

    FILE_NAME_PATTERN = r'<meta name="title" content="(?P<N>.+?)"'
    FILE_SIZE_PATTERN = '<span title="Size: (?P<S>[0-9,.]+) (?P<U>[kKMG])i?B">'
    FILE_OFFLINE_PATTERN = 'The file link that you requested is not valid\.|This file was deleted.'
    FILE_NAME_REPLACEMENTS = [(r"&#(\d+).", lambda m: unichr(int(m.group(1))))]
    FILE_SIZE_REPLACEMENTS = [(",", "")]
    
    DOWNLOAD_BUTTON_PATTERN = 'id="btnLink" href="(.*?)"'
    FID_PATTERN = 'name="d3fid" value="(.*?)"'
    DOWNLOAD_URL_PATTERN = r'name="d3link" value="(.*?)"'

    def handleFree(self):
        if not self.account:
            self.fail("User not logged in")
    
        found = re.search(self.DOWNLOAD_BUTTON_PATTERN, self.html)
        if found:
            link = found.group(1)
        else:
            link = re.sub(r'/(download|get|file|document|photo|video|audio)/', r'/get/', self.pyfile.url)
                   
        self.html = self.load(link)
                
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: self.parseError('Download link')
        link = found.group(1)
        
        try:
            found = re.search(self.FID_PATTERN, self.html)
            response = self.load('http://www.4shared.com/web/d2/getFreeDownloadLimitInfo?fileId=%s' % found.group(1))
            self.logDebug(response)
        except:
            pass
        
        self.setWait(20)
        self.wait()
        self.download(link)

getInfo = create_getInfo(FourSharedCom)            