# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.Crypter import Crypter


class LixIn(Crypter):
    __name__    = "LixIn"
    __type__    = "crypter"
    __version__ = "0.24"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?lix\.in/(?P<ID>.+)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Lix.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("spoob", "spoob@pyload.org")]


    CAPTCHA_PATTERN = r'<img src="(captcha_img\.php\?.*?)"'
    SUBMIT_PATTERN = r'value=\'continue.*?\''
    LINK_PATTERN = r'name="ifram" src="(.*?)"'


    def decrypt(self, pyfile):
        url = pyfile.url

        m = re.match(self.__pattern__, url)
        if m is None:
            self.error(_("Unable to identify file ID"))

        id = m.group('ID')
        self.log_debug("File id is %s" % id)

        self.html = self.load(url)

        m = re.search(self.SUBMIT_PATTERN, self.html)
        if m is None:
            self.error(_("Link doesn't seem valid"))

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m:
            for _i in xrange(5):
                m = re.search(self.CAPTCHA_PATTERN, self.html)
                if m:
                    self.log_debug("Trying captcha")
                    captcharesult = self.captcha.decrypt(urlparse.urljoin("http://lix.in/", m.group(1)))
                self.html = self.load(url,
                                          post={'capt': captcharesult, 'submit': "submit", 'tiny': id})
            else:
                self.log_debug("No captcha/captcha solved")
        else:
            self.html = self.load(url, post={'submit': "submit", 'tiny': id})

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Unable to find destination url"))
        else:
            self.urls = [m.group(1)]
            self.log_debug("Found link %s, adding to package" % self.urls[0])
