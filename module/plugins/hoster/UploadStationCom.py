# -*- coding: utf-8 -*-
from __future__ import with_statement

from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

import re

def getInfo(urls):
    result = []
    
    for url in urls:
        
        # Get file info html
        html = getURL(url) 
        if re.search(UploadStationCom.FILE_OFFLINE_PATTERN, html):
            result.append((url, 0, 1, url))
            continue
        
        # Name
        name = re.search(UploadStationCom.FILE_TITLE_PATTERN, html).group(1)
        
        # Size
        m = re.search(UploadStationCom.FILE_SIZE_PATTERN, html)
        value = float(m.group(1))
        units = m.group(2)
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[units] 
        size = int(value*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result


class UploadStationCom(Hoster):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?uploadstation\.com/file/(?P<id>[A-Za-z0-9]+)"
    __version__ = "0.3"
    __description__ = """UploadStation.Com File Download Hoster"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")
    
    FILE_OFFLINE_PATTERN = r'''<h1>File not available</h1>|<b>The file could not be found\. Please check the download link'''
    FILE_TITLE_PATTERN = r'''<div class=\"download_item\">(.*?)</div>'''
    FILE_SIZE_PATTERN = r'''<div><span>File size: <b>(.*?) (KB|MB|GB)</b>'''
    CAPTCHA_PRESENT_TOKEN = '<div class="speedBox" id="showCaptcha" style="display:none;">'
    CAPTCHA_KEY_PATTERN = r"var reCAPTCHA_publickey='(.*?)';"
    CAPTCHA_WRONG_TOKEN = 'incorrect-captcha-sol'
    WAITING_PATTERN = r".*?(\d+).*?"
    TIME_LIMIT_TOKEN = '"fail":"timeLimit"'
    TIME_LIMIT_WAIT_PATTERN = r"You need to wait (\d+) seconds to download next file."
    DOWNLOAD_RESTRICTION_TOKEN = '"To remove download restriction, please choose your suitable plan as below</h1>"'
        
    def setup(self):
        self.multiDL = False
        self.fileId = ''
        self.html = ''

    def process(self, pyfile):
        
        # Get URL
        self.html = self.load(self.pyfile.url, ref=False, cookies=True, utf8=True)

        # Is offline?
        m = re.search(UploadStationCom.FILE_OFFLINE_PATTERN, self.html) 
        if m is not None:
            self.offline()

        # Id & Title
        self.fileId = re.search(self.__pattern__, self.pyfile.url).group('id')
        self.pyfile.name = re.search(UploadStationCom.FILE_TITLE_PATTERN, self.html).group(1)         

        # Free account
        self.handleFree()
           
    def handleFree(self):
        
        # Not needed yet
        # pattern = r'''\"(/landing/.*?/download_captcha\.js)\"'''
        # jsPage = re.search(pattern, self.html).group(1)
        # self.jsPage = self.load("http://uploadstation.com" + jsPage)
        
        # Check download
        response = self.load(self.pyfile.url, post={"checkDownload" : "check"})
        self.log.debug("%s: Checking download, response [%s]" % (self.__name__, response))
        self.handleErrors(response)
        
        # We got a captcha?
        if UploadStationCom.CAPTCHA_PRESENT_TOKEN in self.html:
            id = re.search(UploadStationCom.CAPTCHA_KEY_PATTERN, self.html).group(1)
            self.log.debug("%s: Resolving ReCaptcha with key [%s]" % (self.__name__, id))
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            response = self.load('http://www.uploadstation.com/checkReCaptcha.php', 
                                  post={'recaptcha_challenge_field' : challenge,
                                        'recaptcha_response_field' : code, 
                                        'recaptcha_shortencode_field' : self.fileId})
            self.log.debug("%s: Result of captcha resolving [%s]" % (self.__name__, response))
            self.handleCaptchaErrors(response)

        # Process waiting
        response = self.load(self.pyfile.url, post={"downloadLink" : "wait"})
        m = re.search(UploadStationCom.WAITING_PATTERN, response)
        if m is not None:
            wait = int(m.group(1))
            if wait == 404:
                self.log.debug("No wait time returned")
                self.fail("No wait time returned")

            self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait))
            self.setWait(wait + 3)
            self.wait()

        # Show download link
        self.load(self.pyfile.url, post={"downloadLink" : "show"})

        # This may either download our file or forward us to an error page
        self.log.debug("%s: Downloading file." % (self.__name__))
        dl = self.download(self.pyfile.url, post={"download" : "normal"})
        self.handleDownloadedFile()
        
    def handleErrors(self, response):
        
        if UploadStationCom.TIME_LIMIT_TOKEN in response:
            wait = 300
            html = self.load(self.pyfile.url, post={"checkDownload" : "showError", "errorType" : "timeLimit"})
            m = re.search(UploadStationCom.TIME_LIMIT_WAIT_PATTERN, html)
            if m is not None:
                wait = int(m.group(1))

            self.log.info("%s: Time limit reached, waiting %d seconds." % (self.__name__, wait))
            self.setWait(wait, True)
            self.wait()
            self.retry()
            
        if UploadStationCom.DOWNLOAD_RESTRICTION_TOKEN in response:
            wait = 720
            self.log.info("%s: Free account time limit reached, waiting %d seconds." % (self.__name__, wait))
            self.setWait(wait, True)
            self.wait()
            self.retry()
            
    def handleCaptchaErrors(self, response):
        if UploadStationCom.CAPTCHA_WRONG_TOKEN in response:
            self.log.info("%s: Invalid captcha response, retrying." % (self.__name__))
            self.invalidCaptcha()
            self.retry()
        else:
            self.correctCaptcha()

    def handleDownloadedFile(self):
        check = self.checkDownload({"wait": re.compile(UploadStationCom.TIME_LIMIT_WAIT_PATTERN)})
        if check == "wait":
            wait = 720
            if self.lastCheck is not None:
                wait = int(self.lastCheck.group(1))
            self.log.debug("%s: Failed, you need to wait %d seconds for another download." % (self.__name__, wait))
            self.setWait(wait + 3, True)
            self.wait()
            self.retry()