#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo
from module.network.RequestFactory import getURL
import re

def getInfo(urls):
    for url in urls:
        html = getURL('http://www.fshare.vn/check_link.php', post = {
            "action" : "check_link",
            "arrlinks" : url
            }, decode = True)

        file_info = parseFileInfo(FshareVn, url, html)

        yield file_info

def doubleDecode(m):
    return m.group(1).decode('raw_unicode_escape')

class FshareVn(SimpleHoster):
    __name__ = "FshareVn"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fshare.vn/file/.*"
    __version__ = "0.13"
    __description__ = """FshareVn Download Hoster"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FILE_INFO_PATTERN = r'<p>(?P<N>[^<]+)<\\/p>[\\trn\s]*<p>(?P<S>[0-9,.]+)\s*(?P<U>[kKMG])i?B<\\/p>'
    FILE_OFFLINE_PATTERN = r'<div class=\\"f_left file_(enable|w)\\">'
    FILE_NAME_REPLACEMENTS = [("(.*)", doubleDecode)] 

    DOWNLOAD_URL_PATTERN = r"<a class=\"bt_down\" id=\"down\".*window.location='([^']+)'\">"
    FORM_PATTERN = r'<form action="" method="post" name="frm_download">(.*?)</form>'
    FORM_INPUT_PATTERN = r'<input[^>]* name="?([^" ]+)"? value="?([^" ]+)"?[^>]*>'
    VIP_URL_PATTERN = r'<form action="([^>]+)" method="get" name="frm_download">'
    WAIT_PATTERN = u"Vui lòng chờ lượt download kế tiếp"

    def process(self, pyfile):
        self.html = self.load('http://www.fshare.vn/check_link.php', post = {
            "action": "check_link",
            "arrlinks": pyfile.url
            }, decode = True)
        self.getFileInfo()
        
        url = self.handlePremium() if self.premium else self.handleFree()
        self.download(url)
        self.checkDownloadedFile()

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode = True)
        if self.WAIT_PATTERN in self.html:
            self.retry(20, 300, "Try again later...")
            
        self.checkErrors()

        found = re.search(self.FORM_PATTERN, self.html, re.DOTALL)
        if not found: self.parseError('FORM')
        form = found.group(1)
        inputs = dict(re.findall(self.FORM_INPUT_PATTERN, form))

        self.html = self.load(self.pyfile.url, post = inputs, decode = True)

        if self.WAIT_PATTERN in self.html:
            self.retry(300, 20, "Try again later...")

        found = re.search(self.DOWNLOAD_URL_PATTERN, self.html)
        if not found: self.parseError('Free URL')
        url = found.group(1)

        found = re.search(r'var count = (\d+)', self.html)
        self.setWait(int(found.group(1)) if found else 30)
        self.wait()

        return url

    def handlePremium(self):
        header = self.load(self.pyfile.url, just_header = True)
        if 'location' in header and header['location'].startswith('http://download'):
            self.logDebug('Direct download')
            return self.pyfile.url
        else:
            self.html = self.load(self.pyfile.url)
            
            self.checkErrors()
            
            found = re.search(self.VIP_URL_PATTERN, self.html)
            if not found:
                if self.retries >= 3: self.resetAccount()
                self.account.relogin(self.user)
                self.retry(5, 1, 'VIP URL not found')
            url = found.group(1)
            self.logDebug('VIP URL: ' + url)
            return url
    
    def checkErrors(self):
        if '/error.php?' in self.req.lastEffectiveURL:
            self.offline()
    
    def checkDownloadedFile(self):
        # check download
        check = self.checkDownload({
            "not_found": ("<head><title>404 Not Found</title></head>")
            })

        if check == "not_found":
            self.fail("File not found on server")