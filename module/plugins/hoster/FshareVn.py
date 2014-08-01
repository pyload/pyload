# -*- coding: utf-8 -*-

import re

from time import strptime, mktime, gmtime

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo


def getInfo(urls):
    for url in urls:
        html = getURL('http://www.fshare.vn/check_link.php', post={
            "action": "check_link",
            "arrlinks": url
        }, decode=True)

        file_info = parseFileInfo(FshareVn, url, html)

        yield file_info


def doubleDecode(m):
    return m.group(1).decode('raw_unicode_escape')


class FshareVn(SimpleHoster):
    __name__ = "FshareVn"
    __type__ = "hoster"
    __version__ = "0.16"

    __pattern__ = r'http://(?:www\.)?fshare.vn/file/.*'

    __description__ = """FshareVn hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FILE_INFO_PATTERN = r'<p>(?P<N>[^<]+)<\\/p>[\\trn\s]*<p>(?P<S>[0-9,.]+)\s*(?P<U>[kKMG])i?B<\\/p>'
    OFFLINE_PATTERN = r'<div class=\\"f_left file_w\\"|<\\/p>\\t\\t\\t\\t\\r\\n\\t\\t<p><\\/p>\\t\\t\\r\\n\\t\\t<p>0 KB<\\/p>'

    FILE_NAME_REPLACEMENTS = [("(.*)", doubleDecode)]

    LINK_PATTERN = r'action="(http://download.*?)[#"]'
    WAIT_PATTERN = ur'Lượt tải xuống kế tiếp là:\s*(.*?)\s*<'


    def process(self, pyfile):
        self.html = self.load('http://www.fshare.vn/check_link.php', post={
            "action": "check_link",
            "arrlinks": pyfile.url
        }, decode=True)
        self.getFileInfo()

        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()
        self.checkDownloadedFile()

    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        self.checkErrors()

        action, inputs = self.parseHtmlForm('frm_download')
        self.url = self.pyfile.url + action

        if not inputs:
            self.parseError('FORM')
        elif 'link_file_pwd_dl' in inputs:
            for password in self.getPassword().splitlines():
                self.logInfo('Password protected link, trying "%s"' % password)
                inputs['link_file_pwd_dl'] = password
                self.html = self.load(self.url, post=inputs, decode=True)
                if not 'name="link_file_pwd_dl"' in self.html:
                    break
            else:
                self.fail("No or incorrect password")
        else:
            self.html = self.load(self.url, post=inputs, decode=True)

        self.checkErrors()

        m = re.search(r'var count = (\d+)', self.html)
        self.setWait(int(m.group(1)) if m else 30)

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.parseError('FREE DL URL')
        self.url = m.group(1)
        self.logDebug("FREE DL URL: %s" % self.url)

        self.wait()
        self.download(self.url)

    def handlePremium(self):
        self.download(self.pyfile.url)

    def checkErrors(self):
        if '/error.php?' in self.req.lastEffectiveURL or u"Liên kết bạn chọn không tồn" in self.html:
            self.offline()

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.logInfo("Wait until %s ICT" % m.group(1))
            wait_until = mktime(strptime(m.group(1), "%d/%m/%Y %H:%M"))
            self.wait(wait_until - mktime(gmtime()) - 7 * 60 * 60, True)
            self.retry()
        elif '<ul class="message-error">' in self.html:
            self.logError("Unknown error occured or wait time not parsed")
            self.retry(30, 2 * 60, "Unknown error")

    def checkDownloadedFile(self):
        # check download
        check = self.checkDownload({
            "not_found": "<head><title>404 Not Found</title></head>"
        })

        if check == "not_found":
            self.fail("File not m on server")
