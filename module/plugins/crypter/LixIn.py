# -*- coding: utf-8 -*-

import re
import urlparse

from ..internal.Crypter import Crypter


class LixIn(Crypter):
    __name__ = "LixIn"
    __type__ = "crypter"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r'http://(?:www\.)?lix\.in/(?P<ID>.+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No", "Create folder for each package", "Default")]

    __description__ = """Lix.in decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("spoob", "spoob@pyload.org")]

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

        self.data = self.load(url)

        m = re.search(self.SUBMIT_PATTERN, self.data)
        if m is None:
            self.error(_("Link doesn't seem valid"))

        m = re.search(self.CAPTCHA_PATTERN, self.data)
        if m is not None:
            captcharesult = self.captcha.decrypt(
                urlparse.urljoin("http://lix.in/", m.group(1)))
            self.data = self.load(
                url,
                post={
                    'capt': captcharesult,
                    'submit': "submit",
                    'tiny': id})

            if re.search(self.CAPTCHA_PATTERN, self.data):
                self.fail(_("No captcha solved"))

        else:
            self.data = self.load(url, post={'submit': "submit", 'tiny': id})

        m = re.search(self.LINK_PATTERN, self.data)
        if m is None:
            self.error(_("Unable to find destination url"))
        else:
            self.links = [m.group(1)]
            self.log_debug("Found link %s, adding to package" % self.links[0])
