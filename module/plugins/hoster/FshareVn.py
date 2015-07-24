# -*- coding: utf-8 -*-

import re
import time
import urlparse

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.SimpleHoster import SimpleHoster, parse_fileInfo


def get_info(urls):
    for url in urls:
        html = get_url("http://www.fshare.vn/check_link.php",
                       post={'action': "check_link", 'arrlinks': url})

        yield parse_fileInfo(FshareVn, url, html)


def double_decode(m):
    return m.group(1).decode('raw_unicode_escape')


class FshareVn(SimpleHoster):
    __name__    = "FshareVn"
    __type__    = "hoster"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fshare\.vn/file/.+'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

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
                              post={'action': "check_link", 'arrlinks': pyfile.url})


    def handle_free(self, pyfile):
        self.html = self.load(pyfile.url)

        self.check_errors()

        action, inputs = self.parse_html_form('frm_download')
        url = urlparse.urljoin(pyfile.url, action)

        if not inputs:
            self.error(_("No FORM"))

        elif 'link_file_pwd_dl' in inputs:
            password = self.get_password()

            if password:
                self.log_info(_("Password protected link, trying ") + password)
                inputs['link_file_pwd_dl'] = password
                self.html = self.load(url, post=inputs)

                if 'name="link_file_pwd_dl"' in self.html:
                    self.fail(_("Incorrect password"))
            else:
                self.fail(_("No password found"))

        else:
            self.html = self.load(url, post=inputs)

        self.check_errors()

        m = re.search(r'var count = (\d+)', self.html)
        self.set_wait(int(m.group(1)) if m else 30)

        m = re.search(self.LINK_FREE_PATTERN, self.html)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = m.group(1)
        self.wait()


    def check_errors(self):
        if '/error.php?' in self.req.lastEffectiveURL or u"Liên kết bạn chọn không tồn" in self.html:
            self.offline()

        m = re.search(self.WAIT_PATTERN, self.html)
        if m:
            self.log_info(_("Wait until %s ICT") % m.group(1))
            wait_until = time.mktime.time(time.strptime.time(m.group(1), "%d/%m/%Y %H:%M"))
            self.wait(wait_until - time.mktime.time(time.gmtime.time()) - 7 * 60 * 60, True)
            self.retry()
        elif '<ul class="message-error">' in self.html:
            msg = "Unknown error occured or wait time not parsed"
            self.log_error(msg)
            self.retry(30, 2 * 60, msg)

        self.info.pop('error', None)
