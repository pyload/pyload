# -*- coding: utf-8 -*-

from __future__ import with_statement

import re

from module.plugins.internal.CaptchaService import ReCaptcha
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class BitshareCom(SimpleHoster):
    __name__ = "BitshareCom"
    __type__ = "hoster"
    __version__ = "0.50"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/(files/(?P<id1>[a-zA-Z0-9]+)(/(?P<name>.*?)\.html)?|\?f=(?P<id2>[a-zA-Z0-9]+))'

    __description__ = """Bitshare.com hoster plugin"""
    __author_name__ = ("Paul King", "fragonib")
    __author_mail__ = ("", "fragonib[AT]yahoo[DOT]es")

    FILE_INFO_PATTERN = r'Downloading (?P<N>.+) - (?P<S>[\d.]+) (?P<U>\w+)</h1>'
    OFFLINE_PATTERN = r'(>We are sorry, but the requested file was not found in our database|>Error - File not available<|The file was deleted either by the uploader, inactivity or due to copyright claim)'

    FILE_AJAXID_PATTERN = r'var ajaxdl = "(.*?)";'
    CAPTCHA_KEY_PATTERN = r'http://api\.recaptcha\.net/challenge\?k=(.*?) '
    TRAFFIC_USED_UP = r'Your Traffic is used up for today. Upgrade to premium to continue!'


    def setup(self):
        self.req.cj.setCookie(".bitshare.com", "language_selection", "EN")
        self.multiDL = self.premium
        self.chunkLimit = 1

    def process(self, pyfile):
        if self.premium:
            self.account.relogin(self.user)

        self.pyfile = pyfile

        # File id
        m = re.match(self.__pattern__, pyfile.url)
        self.file_id = max(m.group('id1'), m.group('id2'))
        self.logDebug("File id is [%s]" % self.file_id)

        # Load main page
        self.html = self.load(pyfile.url, ref=False, decode=True)

        # Check offline
        if re.search(self.OFFLINE_PATTERN, self.html):
            self.offline()

        # Check Traffic used up
        if re.search(self.TRAFFIC_USED_UP, self.html):
            self.logInfo("Your Traffic is used up for today")
            self.wait(30 * 60, True)
            self.retry()

        # File name
        m = re.match(self.__pattern__, pyfile.url)
        name1 = m.group('name') if m else None
        m = re.search(self.FILE_INFO_PATTERN, self.html)
        name2 = m.group('N') if m else None
        pyfile.name = max(name1, name2)

        # Ajax file id
        self.ajaxid = re.search(self.FILE_AJAXID_PATTERN, self.html).group(1)
        self.logDebug("File ajax id is [%s]" % self.ajaxid)

        # This may either download our file or forward us to an error page
        url = self.getDownloadUrl()
        self.logDebug("Downloading file with url [%s]" % url)
        self.download(url)

        check = self.checkDownload({"404": ">404 Not Found<", "Error": ">Error occured<"})
        if check == "404":
            self.retry(3, 60, 'Error 404')
        elif check == "error":
            self.retry(5, 5 * 60, "Bitshare host : Error occured")

    def getDownloadUrl(self):
        # Return location if direct download is active
        if self.premium:
            header = self.load(self.pyfile.url, cookies=True, just_header=True)
            if 'location' in header:
                return header['location']

        # Get download info
        self.logDebug("Getting download info")
        response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                             post={"request": "generateID", "ajaxid": self.ajaxid})
        self.handleErrors(response, ':')
        parts = response.split(":")
        filetype = parts[0]
        wait = int(parts[1])
        captcha = int(parts[2])
        self.logDebug("Download info [type: '%s', waiting: %d, captcha: %d]" % (filetype, wait, captcha))

        # Waiting
        if wait > 0:
            self.logDebug("Waiting %d seconds." % wait)
            if wait < 120:
                self.wait(wait, False)
            else:
                self.wait(wait - 55, True)
                self.retry()

        # Resolve captcha
        if captcha == 1:
            self.logDebug("File is captcha protected")
            id = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group(1)
            # Try up to 3 times
            for i in xrange(3):
                self.logDebug("Resolving ReCaptcha with key [%s], round %d" % (id, i + 1))
                recaptcha = ReCaptcha(self)
                challenge, code = recaptcha.challenge(id)
                response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                                     post={"request": "validateCaptcha", "ajaxid": self.ajaxid,
                                           "recaptcha_challenge_field": challenge, "recaptcha_response_field": code})
                if self.handleCaptchaErrors(response):
                    break

        # Get download URL
        self.logDebug("Getting download url")
        response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                             post={"request": "getDownloadURL", "ajaxid": self.ajaxid})
        self.handleErrors(response, '#')
        url = response.split("#")[-1]

        return url

    def handleErrors(self, response, separator):
        self.logDebug("Checking response [%s]" % response)
        if "ERROR:Session timed out" in response:
            self.retry()
        elif "ERROR" in response:
            msg = response.split(separator)[-1]
            self.fail(msg)

    def handleCaptchaErrors(self, response):
        self.logDebug("Result of captcha resolving [%s]" % response)
        if "SUCCESS" in response:
            self.correctCaptcha()
            return True
        elif "ERROR:SESSION ERROR" in response:
            self.retry()
        self.logDebug("Wrong captcha")
        self.invalidCaptcha()


getInfo = create_getInfo(BitshareCom)
