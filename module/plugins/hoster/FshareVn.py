#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
import re

class FshareVn(SimpleHoster):
    __name__ = "FshareVn"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fshare.vn/file/.*"
    __version__ = "0.10"
    __description__ = """FshareVn Download Hoster"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = ur'<p><b>Tên file:</b>\s*(?P<N>[^<]+)</p>\s*<p><b>Dung lượng file:</b>\s*(?P<S>[0-9,.]+)\s*(?P<U>[kKMG])i?B</p>'
    FILE_OFFLINE_PATTERN = r'<span class="error_number">511</span>'
    
    DOWNLOAD_URL_PATTERN = r"<a class=\"bt_down\" id=\"down\".*window.location='([^']+)'\">"
    FORM_PATTERN = r'<form action="" method="post" name="frm_download">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="?([^" ]+)"? value="?([^" ]+)"?[^>]*>'

    def handleFree(self):
        found = re.search(self.FORM_PATTERN, self.html, re.DOTALL)
        if not found: self.parseError('FORM')
        form = found.group(1)
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))
        
        self.html = self.load(self.pyfile.url, post = inputs)
                
        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: self.parseError('Free URL')
        url = found.group(1)
        
        found = re.search(r'var count = (\d+)', self.html)
        self.setWait(int(found.group(1)) if found else 30)
        self.wait()
        
        self.download(url)

getInfo = create_getInfo(FshareVn)
            