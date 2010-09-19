# -*- coding: utf-8 -*-

import re

from os.path import join

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.network.Request import getURL

def getInfo(urls):
    result = []
    
    for url in urls:
        html = getURL(url)
        if re.search(r'<h1>File not available</h1>', html):
            result.append((url, 0, 1, url))
            continue
        
        size = re.search(r"<span><strong>(.*?) MB</strong>", html).group(1)
        size = int(float(size)*1024*1024)
        
        name = re.search('<h1>(.*?)<br/></h1>', html).group(1)
        result.append((name, size, 2, url))
        
    yield result

class FileserveCom(Hoster):
    __name__ = "FileserveCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fileserve\.com/file/.*?(/.*)?"
    __version__ = "0.2"
    __description__ = """Fileserve.Com File Download Hoster"""
    __author_name__ = ("jeix", "mkaay")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de")
        
    def setup(self):
        self.req.canContinue = self.multiDL = True if self.account else False
        
    def process(self, pyfile):
        
        self.html = self.load(self.pyfile.url, cookies=False if self.account else True)
        if re.search(r'<h1>File not available</h1>', self.html) is not None:
            self.offline()
            
        self.pyfile.name = re.search('<h1>(.*?)<br/></h1>', self.html).group(1)
        
        if self.account:
            self.handlePremium()
        else:
            self.handleFree()
    
    def handlePremium(self):
        self.download(self.pyfile.url, post={"download":"premium"}, cookies=True)
    
    def handleFree(self):
        
        if r'<div id="captchaArea" style="display:none;">' in self.html or \
           r'/showCaptcha\(\);' in self.html:
            # we got a captcha
            id = re.search(r"var reCAPTCHA_publickey='(.*?)';", self.html).group(1)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            
            shortencode = re.search(r'name="recaptcha_shortencode_field" value="(.*?)"', self.html).group(1)

            self.html = self.load(r'http://www.fileserve.com/checkReCaptcha.php', post={'recaptcha_challenge_field':challenge,
                'recaptcha_response_field':code, 'recaptcha_shortencode_field': shortencode})
                
            if r'incorrect-captcha-sol' in self.html:
                self.retry()

        html = self.load(self.pyfile.url, post={"downloadLink":"wait"})
       
        wait_time = 30
        m = re.search(r'<span>(.*?)\sSekunden</span>', html)
        if m is not None:
            wait_time = int( m.group(1).split('.')[0] ) + 1
            
        m = re.search(r'You need to wait (.*?) seconds to start another download.', html)
        if m is not None:
            wait_time = int( m.group(1) )
            self.wantReconnect = True
            
        if r'Your download link has expired.' in html:
            self.retry()
       
        self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait_time))
        self.setWait(wait_time)
        self.wait()
        
        self.load(self.pyfile.url, post={"downloadLink":"show"})

        self.load(self.pyfile.url, post={"download":"normal"}, just_header=True)
        self.download(self.pyfile.url, post={"download":"normal"})


        #TODO: validate download it could be html file with errors
