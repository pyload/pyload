# -*- coding: utf-8 -*-
from __future__ import with_statement

import re
import unicodedata

from os import remove

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.network.RequestFactory import getURL

def unicode2str(unitext):
    return unicodedata.normalize('NFKD', unitext).encode('ascii', 'ignore') 

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
        value = float(m.group(1))
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[m.group(2)] 
        size = int(value*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result


class UploadStationCom(Hoster):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?uploadstation\.com/file/[A-Za-z0-9]+"
    __version__ = "0.2"
    __description__ = """UploadStation.Com File Download Hoster"""
    __author_name__ = ("fragonib")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es")
        
    def setup(self):
        self.multiDL = False
        self.fileId = re.search(r"uploadstation\.com/file/([a-zA-Z0-9]+)(http:.*)?", self.pyfile.url).group(1)
        self.pyfile.url = "http://www.uploadstation.com/file/" + self.fileId

    def process(self, pyfile):
        
        # Get URL
        self.html = self.load(self.pyfile.url, ref=False, cookies=True, utf8=True)

        # Is offline?
        pattern = r'''<h1>File not available</h1>|<b>The file could not be found\. Please check the download link'''
        m = re.search(pattern, self.html) 
        if m is not None:
            self.offline()

        # Title
        pattern = r'''<div class=\"download_item\">(.*?)</div>'''
        title = re.search(pattern, self.html).group(1)
        self.pyfile.name = unicode2str(title)            

        # Free account
        self.handleFree()
           
    def handleFree(self):
        
        # Not needed yet
        #pattern = r'''\"(/landing/.*?/download_captcha\.js)\"'''
        #jsPage = re.search(pattern, self.html).group(1)
        #self.jsPage = self.load("http://uploadstation.com" + jsPage)
        
        # Check download
        response = self.load(self.pyfile.url, post={"checkDownload" : "check"})
        if not '"success":"showCaptcha"' in response:
            self.handleErrors(response)
        
        # We got a captcha?
        if '<div class="speedBox" id="showCaptcha" style="display:none;">' in self.html:
            id = re.search(r"var reCAPTCHA_publickey='(.*?)';", self.html).group(1)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            response = self.load('http://www.uploadstation.com/checkReCaptcha.php', 
                                  post={'recaptcha_challenge_field' : challenge,
                                        'recaptcha_response_field' : code, 
                                        'recaptcha_shortencode_field' : self.fileId})
            if r'incorrect-captcha-sol' in response:
                self.handleCaptchaErrors(response)

        # Process waiting
        response = self.load(self.pyfile.url, post={"downloadLink":"wait"})
        m = re.search(r".*?(\d+).*?", response)
        if m is not None:
            wait = m.group(1)
            if wait == "404":
                self.log.debug("No wait time returned")
                self.fail("No wait time returned")
            else:
                self.setWait(int(wait))

            self.wait()

        # Show download link
        self.load(self.pyfile.url, post={"downloadLink":"show"})

        # This may either download our file or forward us to an error page
        dl = self.download(self.pyfile.url, post={"download":"normal"})
        self.handleDownloadedFile()
        
    def handleErrors(self, response):
        
        text = '"fail":"timeLimit"'
        if text in response:
            wait = 300
            html = self.load(self.pyfile.url, post={"checkDownload" : "showError", "errorType" : "timeLimit"})
            m = re.search(r"You need to wait (\d+) seconds to download next file.", html)
            if m is not None:
                wait = int(m.group(1))

            self.setWait(wait, True)
            self.wait()
            self.retry()
            
        text = '"To remove download restriction, please choose your suitable plan as below</h1>"'
        if text in response:
            wait = 720
            self.setWait(wait, True)
            self.wait()
            self.retry()
            
    def handleCaptchaErrors(self, response):
        self.invalidCaptcha()
        self.retry()

    def handleDownloadedFile(self):
        check = self.checkDownload({"wait": re.compile(r'You need to wait (\d+) seconds to download next file.')})
        
        if check == "wait":
            wait_time = 720
            if self.lastCheck is not None:
                wait_time = int(self.lastCheck.group(1))
            self.setWait(wait_time+3)
            self.log.debug("%s: You need to wait %d seconds for another download." % (self.__name__, wait_time))
            self.wantReconnect = True
            self.wait()
            self.retry() 