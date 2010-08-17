# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

class FileserveCom(Hoster):
    __name__ = "FileserveCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fileserve\.com/file/.*?(/.*)?"
    __version__ = "0.1"
    __description__ = """Fileserve.Com File Download Hoster"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")
        
    def setup(self):
        self.multiDL = False
        
    def process(self, pyfile):
        
        html = self.load(self.pyfile.url)
        if re.search(r'<h1>File not available</h1>', html) != None:
            self.offline
            
        self.pyfile.name = re.search('<h1>(.*?)<br/></h1>', html).group(1)
                    
        if r'<div id="captchaArea" style="display:none;">' in html or \
           r'/showCaptcha\(\);' in html:
            # we got a captcha
            id = re.search(r"var reCAPTCHA_publickey='(.*?)';", html).group(1)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            
            shortencode = re.search(r'name="recaptcha_shortencode_field" value="(.*?)"', html).group(1)

            html = self.load(r'http://www.fileserve.com/checkReCaptcha.php', post={'recaptcha_challenge_field':challenge,
                'recaptcha_response_field':code, 'recaptcha_shortencode_field': shortencode})
                
            if r'incorrect-captcha-sol' in html:
                self.retry()

        html = self.load(self.pyfile.url, post={"downloadLink":"wait"})
       
        wait_time = 30
        m = re.search(r'<span>(.*?)\sSekunden</span>', html)
        if m != None:
            wait_time = int( m.group(1).split('.')[0] ) + 1
            
        m = re.search(r'You need to wait (.*?) seconds to start another download.', html)
        if m != None:
            wait_time = int( m.group(1) )
            self.wantReconnect = True
            
        if r'Your download link has expired.' in html:
            self.retry()
       
        self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait_time))
        self.setWait(wait_time)
        self.wait()
        
        self.load(self.pyfile.url, post={"downloadLink":"show"})
        
        self.log.debug("%s: Downloading." % self.__name__)
        self.download(self.pyfile.url, post={"download":"normal"})
