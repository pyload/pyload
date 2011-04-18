# -*- coding: utf-8 -*-
from __future__ import with_statement

import re
import unicodedata

from os import remove

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []
    
    for url in urls:
        
        # Get html
        html = getURL(url)
        pattern = r'''<h1>File not available</h1>|<b>The file could not be found\. Please check the download link'''  
        if re.search(pattern, html):
            result.append((url, 0, 1, url))
            continue
        
        # Name
        pattern = r'''<div class=\"download_item\">(.*?)</div>'''
        name = re.search(pattern, html).group(1)
        
        # Size
        pattern = r'''<div><span>File size: <b>(.*?) (KB|MB|GB)</b>'''
        m = re.search(pattern, html)
        units = float(m.group(1))
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[m.group(2)] 
        size = int(units*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result

class UploadStationCom(Hoster):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?uploadstation\.com/file/[A-Za-z0-9]+"
    __version__ = "0.1"
    __description__ = """UploadStation.Com File Download Hoster"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")
        
    def setup(self):
        self.multiDL = False
        self.file_id = re.search(r"uploadstation\.com/file/([a-zA-Z0-9]+)(http:.*)?", self.pyfile.url).group(1)
        self.pyfile.url = "http://www.uploadstation.com/file/" + self.file_id

    def process(self, pyfile):
        self.html = self.load(self.pyfile.url, ref=False, cookies=False if self.account else True, utf8=True)

        pattern = r'''<h1>File not available</h1>|<b>The file could not be found\. Please check the download link''' 
        if re.search(pattern, self.html):
            self.offline()

        pattern = r'''<div class=\"download_item\">(.*?)</div>'''
        title = re.search(pattern, self.html).group(1)
        self.pyfile.name = unicodedata.normalize('NFKD', title).encode('ascii','ignore')            

        self.handleFree()
           
    def handleFree(self):

        self.html = self.load(self.pyfile.url)
        
        # Not needed yet
        #jsPage = re.search(r"\"(/landing/.*?/download_captcha\.js)\"", self.html)
        #jsPage = self.load("http://uploadstation.com" + jsPage.group(1))
        
        self.action = self.load(self.pyfile.url, post={"checkDownload" : "check"})
        if "success\":\"showCaptcha\"" in self.action:
            self.handleErrors()
        
        if r'<div class="speedBox" id="showCaptcha" style="display:none;">' in self.html:
            # we got a captcha
            id = re.search(r"var reCAPTCHA_publickey='(.*?)';", self.html).group(1)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            
            self.html = self.load(r'http://www.uploadstation.com/checkReCaptcha.php', post={'recaptcha_challenge_field':challenge,
                'recaptcha_response_field':code, 'recaptcha_shortencode_field': self.file_id})
                
            if r'incorrect-captcha-sol' in self.html:
                self.invalidCaptcha()
                self.retry()

        wait = self.load(self.pyfile.url, post={"downloadLink":"wait"})
        wait = re.search(r".*?(\d+).*?", wait)
        if wait:
            wait = wait.group(1)
            if wait == "404":
                self.log.debug("No wait time returned")
                self.fail("No wait time returned")
            else:
                self.setWait(int(wait))

            self.wait()

        # show download link
        self.load(self.pyfile.url, post={"downloadLink":"show"})

        # this may either download our file or forward us to an error page
        dl = self.download(self.pyfile.url, post={"download":"normal"})
        self.handleDownload()
        
    def handleErrors(self):
        if "timeLimit" in self.action:
            html = self.load(self.pyfile.url, post={"checkDownload" : "showError", "errorType" : "timeLimit"})
            wait = re.search(r"You need to wait (\d+) seconds to start another download", html)
            if wait:
                wait = int(wait.group(1))
            else:
                wait = 720

            self.setWait(wait, True)
            self.wait()
            self.retry()

    def handleDownload(self):
        check = self.checkDownload({"expired": "Your download link has expired",
                                    "wait": re.compile(r'You need to wait (\d+) seconds to start another download')})
        if check == "expired":
            self.retry()
        elif check == "wait":
            wait_time = 720
            if self.lastCheck is not None:
                wait_time = int(self.lastCheck.group(1))
            self.setWait(wait_time+3)
            self.log.debug("%s: You need to wait %d seconds for another download." % (self.__name__, wait_time))
            self.wantReconnect = True
            self.wait()
            self.retry()