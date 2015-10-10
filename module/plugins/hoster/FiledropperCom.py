# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class FiledropperCom(SimpleHoster):
    __name__    = "FiledropperCom"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?filedropper\.com/\w+'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Filedropper.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zapp-brannigan", "fuerst.reinje@web.de")]


    NAME_PATTERN    = r'Filename: (?P<N>.+?) <'
    SIZE_PATTERN    = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+),'  #@NOTE: Website says always 0 KB
    OFFLINE_PATTERN = r'value="a\.swf"'


    def setup(self):
        self.multiDL    = False
        self.chunk_limit = 1


    def handle_free(self, pyfile):
        m = re.search(r'img id="img" src="(.+?)"', self.html)
        if m is None:
            self.fail(_("Captcha not found"))

        captcha_code = self.captcha.decrypt("http://www.filedropper.com/%s" % m.group(1))

        m = re.search(r'method="post" action="(.+?)"', self.html)
        if m is not None:
            self.download(urlparse.urljoin("http://www.filedropper.com/", m.group(1)),
                          post={'code': captcha_code})


getInfo = create_getInfo(FiledropperCom)
