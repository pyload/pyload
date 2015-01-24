# -*- coding: utf-8 -*-

import re

from time import strptime, mktime, gmtime
from urlparse import urljoin

from module.network.RequestFactory import getURL
from module.plugins.internal.SimpleHoster import SimpleHoster, parseFileInfo


def getInfo(urls):
    for url in urls:
        html = getURL("http://www.fshare.vn/check_link.php",
                      post={'action': "check_link", 'arrlinks': url},
                      decode=True)

        yield parseFileInfo(FshareVn, url, html)


def doubleDecode(m):
    return m.group(1).decode('raw_unicode_escape')


class FshareVn(SimpleHoster):
    __name__    = "FshareVn"
    __type__    = "hoster"
    __version__ = "0.20"

    __pattern__ = r'http://(?:www\.)?fshare\.vn/file/.+'

    __description__ = """FshareVn hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN = r'<p>(?P<N>[^<]+)<\\/p>[\\trn\s]*<p>(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)<\\/p>'
    OFFLINE_PATTERN = r'<div class=\\"f_left file_w\\"|<\\/p>\\t\\t\\t\\t\\r\\n\\t\\t<p><\\/p>\\t\\t\\r\\n\\t\\t<p>0 KB<\\/p>'

    NAME_REPLACEMENTS = [("(.*)", doubleDecode)]

    LINK_FREE_PATTERN = r'action="(http://download.*?)[#"]'
    WAIT_PATTERN = ur'Lượt tải xuống kế tiếp là:\s*(.*?)\s*<'


    def preload(self):
        self.html = self.load("http://www.fshare.vn/check_link.php",
                              post={'action': "check_link", 'arrlinks': pyfile.url},
                              decode=True)

        if isinstance(self.TEXT_ENCODING, basestring):
            self.html = unicode(self.html, self.TEXT_ENCODING)


    def handleFree(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        self.checkErrors()

        action, inputs = self.parseHtmlForm('frm_download')
        url = urljoin(pyfile.url, action)

        if not inputs:
            self.error(_("No FORM"))

        elif 'link_file_pwd_dl' in inputs:
            password = self.getPassword()

            if password:
                self.logInfo(_("Password protected link, trying ") + password)
                inputs['link_file_pwd_dl'] = password
                self.html = self.load(url, post=inputs, decode=True)

                if 'name="link_file_pwd_dl"' in self.html:
                    self.fail(_("Incorrect password"))
            else:
                self.fail(_("No password found"))

        else:
            self.html = self.load(url, post=inputs, decode=True)

        self.checkErrors()

        m = re.search(r'var count = (\d+)', self.html)
        self.setWait(int(m.group(1)) if m else 30)

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))
        
        self.link = m.group(1)
        self.wait()


    def checkErrors(self):
        if '/error.php?' in self.req.lastEffectiveURL or u"Liên kết bạn chọn không tồn" in self.html:
            self.offline()

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.logInfo(_("Wait until %s ICT") % m.group(1))
            wait_until = mktime(strptime(m.group(1), "%d/%m/%Y %H:%M"))
            self.wait(wait_until - mktime(gmtime()) - 7 * 60 * 60, True)
            self.retry()
        elif '<ul class="message-error">' in self.html:
            msg = "Unknown error occured or wait time not parsed"
            self.logError(msg)
            self.retry(30, 2 * 60, msg)

        self.info.pop('error', None)
