# -*- coding: utf-8 -*-
#
# Test links:
# http://ul.to/044yug9o
# http://ul.to/gzfhd0xs

import re

from time import sleep

from module.network.RequestFactory import getURL
from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class UploadedTo(SimpleHoster):
    __name__    = "UploadedTo"
    __type__    = "hoster"
    __version__ = "0.79"

    __pattern__ = r'https?://(?:www\.)?(uploaded\.(to|net)|ul\.to)(/file/|/?\?id=|.*?&id=|/)(?P<ID>\w+)'

    __description__ = """Uploaded.net hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    API_KEY = "bGhGMkllZXByd2VEZnU5Y2NXbHhYVlZ5cEE1bkEzRUw="  #@NOTE: base64 encoded

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://uploaded.net/file/\g<ID>')]

    INFO_PATTERN    = r'<a href="file/(?P<ID>\w+)" id="filename">(?P<N>[^<]+)</a> &nbsp;\s*<small[^>]*>(?P<S>[^<]+)</small>'
    OFFLINE_PATTERN = r'<small class="cL">Error: 404'

    LINK_PREMIUM_PATTERN = r'<div class="tfree".*\s*<form method="post" action="(.+?)"'

    DL_LIMIT_ERROR = r'You have reached the max. number of possible free downloads for this hour'


    @classmethod
    def apiInfo(cls, url="", get={}, post={}):
        info = super(UploadedTo, cls).apiInfo(url)

        for _i in xrange(5):
            api = getURL("http://uploaded.net/api/filemultiple",
                         post={"apikey": cls.API_KEY.decode('base64'), 'id_0': re.match(cls.__pattern__, url).group('ID')},
                         decode=True)
            if api != "can't find request":
                api = api.splitlines()[0].split(",", 4)

                if api[0] == "online":
                    info.update({'name': api[4], 'size': api[2], 'status': 2})

                elif api[0] == "offline":
                    info['status'] = 1

                break
            else:
                sleep(3)

        return info


    def setup(self):
        self.multiDL    = self.resumeDownload = self.premium
        self.chunkLimit = 1  # critical problems with more chunks
        self.load("http://uploaded.net/language/en", just_header=True)


    def checkErrors(self):
        if 'var free_enabled = false;' in self.html:
            self.logError(_("Free-download capacities exhausted"))
            self.retry(24, 5 * 60)

        if not self.premium:
            m = re.search(r"Current waiting period: <span>(\d+)</span> seconds", self.html)
            if m:
                self.wait(m.group(1))
            else:
                self.fail(_("File not downloadable for free users"))

        if "limit-size" in self.html:
            self.fail(_("File too big for free download"))

        elif "limit-slot" in self.html:  # Temporary restriction so just wait a bit
            self.wait(30 * 60, True)
            self.retry()

        elif "limit-parallel" in self.html:
            self.fail(_("Cannot download in parallel"))

        elif "limit-dl" in self.html or self.DL_LIMIT_ERROR in self.html:  # limit-dl
            self.wait(3 * 60 * 60, True)
            self.retry()

        elif '"err":"captcha"' in self.html:
            self.invalidCaptcha()


    def handleFree(self, pyfile):
        self.html = self.load("http://uploaded.net/js/download.js", decode=True)

        recaptcha = ReCaptcha(self)
        response, challenge = recaptcha.challenge()

        self.html = self.load("http://uploaded.net/io/ticket/captcha/%s" % self.info['pattern']['ID'],
                              post={'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field' : response})

        if "type:'download'" in self.html:
            self.correctCaptcha()
            try:
                self.link = re.search("url:'([^']+)", self.html).group(1)

            except Exception:
                pass

        self.checkErrors()


    def checkFile(self):
        if self.checkDownload({'limit-dl': self.DL_LIMIT_ERROR}):
            self.wait(3 * 60 * 60, True)
            self.retry()

        return super(UploadedTo, self).checkFile()


getInfo = create_getInfo(UploadedTo)
