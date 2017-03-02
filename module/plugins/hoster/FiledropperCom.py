# -*- coding: utf-8 -*-

import re
import urlparse

from ..internal.SimpleHoster import SimpleHoster


class FiledropperCom(SimpleHoster):
    __name__ = "FiledropperCom"
    __type__ = "hoster"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?filedropper\.com/\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Filedropper.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zapp-brannigan", "fuerst.reinje@web.de")]

    NAME_PATTERN = r'Filename: (?P<N>.+?) <'
    # @NOTE: Website says always 0 KB
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+),'
    OFFLINE_PATTERN = r'value="a\.swf"'

    def setup(self):
        self.multiDL = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        m = re.search(r'img id="img" src="(.+?)"', self.data)
        if m is None:
            self.fail(_("Captcha not found"))

        captcha_code = self.captcha.decrypt(
            "http://www.filedropper.com/%s" %
            m.group(1))

        m = re.search(r'method="post" action="(.+?)"', self.data)
        if m is not None:
            self.download(urlparse.urljoin("http://www.filedropper.com/", m.group(1)),
                          post={'code': captcha_code})
