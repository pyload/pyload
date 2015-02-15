# -*- coding: utf-8 -*-

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class ZippyshareCom(SimpleHoster):
    __name__    = "ZippyshareCom"
    __type__    = "hoster"
    __version__ = "0.72"

    __pattern__ = r'http://www\d{0,2}\.zippyshare\.com/v(/|iew\.jsp.*key=)(?P<KEY>[\w^_]+)'

    __description__ = """Zippyshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("zippyshare.com", "ziplocale", "en")]

    NAME_PATTERN    = r'("\d{6,}/"[ ]*\+.+?"/|<title>Zippyshare.com - )(?P<N>.+?)("|</title>)'
    SIZE_PATTERN    = r'>Size:.+?">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File does not exist on this server'

    LINK_PREMIUM_PATTERN = r'document.location = \'(.+?)\''


    def setup(self):
        self.chunkLimit     = -1
        self.multiDL        = True
        self.resumeDownload = True


    def handleFree(self, pyfile):
        recaptcha   = ReCaptcha(self)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            try:
                self.link = re.search(self.LINK_PREMIUM_PATTERN, self.html)
                recaptcha.challenge()

            except Exception, e:
                self.error(e)

        else:
            self.link = '/'.join(("d", self.info['pattern']['KEY'], str(self.get_checksum()), self.pyfile.name))


    def get_checksum(self):
        try:
            n = 2
            b = int(re.search(r'var b = (\d+)', self.html).group(1))
            checksum = int("%d3" % (n + n * 2 + b))

        except Exception:
            self.error(_("Unable to calculate checksum"))

        else:
            return checksum


getInfo = create_getInfo(ZippyshareCom)
