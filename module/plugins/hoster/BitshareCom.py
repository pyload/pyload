# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BitshareCom(SimpleHoster):
    __name__    = "BitshareCom"
    __type__    = "hoster"
    __version__ = "0.55"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/(files/)?(?(1)|\?f=)(?P<ID>\w+)(?(1)/(?P<NAME>.+?)\.html)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Bitshare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Paul King", None),
                       ("fragonib", "fragonib[AT]yahoo[DOT]es")]


    COOKIES = [("bitshare.com", "language_selection", "EN")]

    INFO_PATTERN    = r'Downloading (?P<N>.+) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)</h1>'
    OFFLINE_PATTERN = r'[Ff]ile (not available|was deleted|was not found)'

    AJAXID_PATTERN  = r'var ajaxdl = "(.*?)";'
    TRAFFIC_USED_UP = r'Your Traffic is used up for today'


    def setup(self):
        self.multiDL    = self.premium
        self.chunk_limit = 1


    def process(self, pyfile):
        if self.premium:
            self.account.relogin(self.user)

        #: File id
        m = re.match(self.__pattern__, pyfile.url)
        self.file_id = max(m.group('ID1'), m.group('ID2'))
        self.log_debug("File id is [%s]" % self.file_id)

        #: Load main page
        self.html = self.load(pyfile.url, ref=False)

        #: Check offline
        if re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()

        #: Check Traffic used up
        if re.search(self.TRAFFIC_USED_UP, self.html):
            self.log_info(_("Your Traffic is used up for today"))
            self.wait(30 * 60, True)
            self.retry()

        #: File name
        m     = re.match(self.__pattern__, pyfile.url)
        name1 = m.group('NAME') if m else None

        m     = re.search(self.INFO_PATTERN, self.html)
        name2 = m.group('N') if m else None

        pyfile.name = max(name1, name2)

        #: Ajax file id
        self.ajaxid = re.search(self.AJAXID_PATTERN, self.html).group(1)
        self.log_debug("File ajax id is [%s]" % self.ajaxid)

        #: This may either download our file or forward us to an error page
        self.link = self.get_download_url()

        if self.check_download({'error': ">Error occured<"}):
            self.retry(5, 5 * 60, "Bitshare host : Error occured")


    def get_download_url(self):
        #: Return location if direct download is active
        if self.premium:
            header = self.load(self.pyfile.url, just_header=True)
            if 'location' in header:
                return header['location']

        #: Get download info
        self.log_debug("Getting download info")
        res = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                        post={'request': "generateID", 'ajaxid': self.ajaxid})

        self.handle_errors(res, ':')

        parts    = res.split(":")
        filetype = parts[0]
        wait     = int(parts[1])
        captcha  = int(parts[2])

        self.log_debug("Download info [type: '%s', waiting: %d, captcha: %d]" % (filetype, wait, captcha))

        #: Waiting
        if wait > 0:
            self.log_debug("Waiting %d seconds." % wait)
            if wait < 120:
                self.wait(wait, False)
            else:
                self.wait(wait - 55, True)
                self.retry()

        #: Resolve captcha
        if captcha == 1:
            self.log_debug("File is captcha protected")
            recaptcha = ReCaptcha(self)

            #: Try up to 3 times
            for i in xrange(3):
                response, challenge = recaptcha.challenge()
                res = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                                     post={'request'                  : "validateCaptcha",
                                           'ajaxid'                   : self.ajaxid,
                                           'recaptcha_challenge_field': challenge,
                                           'recaptcha_response_field' : response})
                if self.handle_captcha_errors(res):
                    break

        #: Get download URL
        self.log_debug("Getting download url")
        res = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                        post={'request': "getDownloadURL", 'ajaxid': self.ajaxid})

        self.handle_errors(res, '#')

        url = res.split("#")[-1]

        return url


    def handle_errors(self, res, separator):
        self.log_debug("Checking response [%s]" % res)
        if "ERROR:Session timed out" in res:
            self.retry()
        elif "ERROR" in res:
            msg = res.split(separator)[-1]
            self.fail(msg)


    def handle_captcha_errors(self, res):
        self.log_debug("Result of captcha resolving [%s]" % res)
        if "SUCCESS" in res:
            self.captcha.correct()
            return True
        elif "ERROR:SESSION ERROR" in res:
            self.retry()

        self.captcha.invalid()


getInfo = create_getInfo(BitshareCom)
