# -*- coding: utf-8 -*-

import re
import time
import urlparse

from module.network.RequestFactory import getURL as get_url
from module.plugins.internal.Base import parse_fileInfo
from module.plugins.internal.SimpleHoster import SimpleHoster


def double_decode(m):
    return m.group(1).decode('raw_unicode_escape')


class FshareVn(SimpleHoster):
    __name__    = "FshareVn"
    __type__    = "hoster"
    __version__ = "0.25"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?fshare\.vn/file/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """FshareVn hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    INFO_PATTERN    = r'<p>(?P<N>.+?)<\\/p>[\\trn\s]*<p>(?P<S>[\d.,]+)\s*(?P<U>[\w^_]+)<\\/p>'
    OFFLINE_PATTERN = r'<div class=\\"f_left file_w\\"|<\\/p>\\t\\t\\t\\t\\r\\n\\t\\t<p><\\/p>\\t\\t\\r\\n\\t\\t<p>0 KB<\\/p>'

    NAME_REPLACEMENTS = [("(.*)", double_decode)]

    LINK_FREE_PATTERN = r'action="(http://download.*?)[#"]'
    WAIT_PATTERN = ur'Lượt tải xuống kế tiếp là:\s*(.*?)\s*<'


    def preload(self):
        self.data = self.load("http://www.fshare.vn/check_link.php",
                              post={'action': "check_link", 'arrlinks': pyfile.url})


    def handle_free(self, pyfile):
        self.data = self.load(pyfile.url)

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
                self.data = self.load(url, post=inputs)

                if 'name="link_file_pwd_dl"' in self.data:
                    self.fail(_("Wrong password"))
            else:
                self.fail(_("No password found"))

        else:
            self.data = self.load(url, post=inputs)

        self.check_errors()

        m = re.search(r'var count = (\d+)', self.data)
        self.set_wait(int(m.group(1)) if m else 30)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is None:
            self.error(_("LINK_FREE_PATTERN not found"))

        self.link = m.group(1)
        self.wait()


    def check_errors(self):
        if '/error.php?' in self.req.lastEffectiveURL or u"Liên kết bạn chọn không tồn" in self.data:
            self.offline()

        m = re.search(self.WAIT_PATTERN, self.data)
        if m is not None:
            self.log_info(_("Wait until %s ICT") % m.group(1))
            wait_until = time.mktime.time(time.strptime.time(m.group(1), "%d/%m/%Y %H:%M"))
            self.wait(wait_until - time.mktime.time(time.gmtime.time()) - 7 * 60 * 60, True)
            self.retry()
        elif '<ul class="message-error">' in self.data:
            msg = "Unknown error occured or wait time not parsed"
            self.log_error(msg)
            self.retry(30, 2 * 60, msg)

        self.info.pop('error', None)
