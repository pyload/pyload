# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter


class LixIn(Crypter):
    __name__ = "LixIn"
    __type__ = "crypter"
    __version__ = "0.22"

    __pattern__ = r'http://(www.)?lix.in/(?P<id>.*)'

    __description__ = """Lix.in decrypter plugin"""
    __author_name__ = "spoob"
    __author_mail__ = "spoob@pyload.org"

    CAPTCHA_PATTERN = r'<img src="(?P<image>captcha_img.php\?.*?)"'
    SUBMIT_PATTERN = r"value='continue.*?'"
    LINK_PATTERN = r'name="ifram" src="(?P<link>.*?)"'


    def decrypt(self, pyfile):
        url = pyfile.url

        m = re.match(self.__pattern__, url)
        if m is None:
            self.fail("couldn't identify file id")

        id = m.group("id")
        self.logDebug("File id is %s" % id)

        self.html = self.req.load(url, decode=True)

        m = re.search(self.SUBMIT_PATTERN, self.html)
        if m is None:
            self.fail("link doesn't seem valid")

        m = re.search(self.CAPTCHA_PATTERN, self.html)
        if m:
            for _ in xrange(5):
                m = re.search(self.CAPTCHA_PATTERN, self.html)
                if m:
                    self.logDebug("trying captcha")
                    captcharesult = self.decryptCaptcha("http://lix.in/" + m.group("image"))
                self.html = self.req.load(url, decode=True,
                                          post={"capt": captcharesult, "submit": "submit", "tiny": id})
            else:
                self.logDebug("no captcha/captcha solved")
        else:
            self.html = self.req.load(url, decode=True, post={"submit": "submit", "tiny": id})

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.fail("can't find destination url")
        else:
            self.urls = [m.group("link")]
            self.logDebug("Found link %s, adding to package" % self.urls[0])
