# -*- coding: utf-8 -*-
from __future__ import with_statement

import re

from os import remove

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.network.RequestFactory import getURL

def getInfo(urls):
    result = []
    
    for url in urls:
        
        # Get html
        html = getURL(url)
        if re.search(r'<h1>File not available</h1>', html):
            result.append((url, 0, 1, url))
            continue
        
        # Name
        name = re.search('<h1>(.*?)<br/></h1>', html).group(1)
        
        # Size
        m = re.search(r"<strong>(.*?) (KB|MB|GB)</strong>", html)
        units = float(m.group(1))
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[m.group(2)] 
        size = int(units*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result

class FileserveCom(Hoster):
    __name__ = "FileserveCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fileserve\.com/file/.*?(/.*)?"
    __version__ = "0.3"
    __description__ = """Fileserve.Com File Download Hoster"""
    __author_name__ = ("jeix", "mkaay")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de")
        
    def setup(self):
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]
            if not self.premium:
                self.multiDL = False
                self.resumeDownload = False
                self.chunkLimit = 1
        else:
            self.multiDL = False

    def process(self, pyfile):
        self.html = self.load(self.pyfile.url, ref=False, cookies=False if self.account else True, utf8=True)

        if re.search(r'<h1>File not available</h1>', self.html) is not None:
            self.offline()
            
        if 'Your download link has expired' in self.html:
            with open("fsdump.html", "w") as fp:
                fp.write(self.html)
            self.offline()#retry()
            
        self.pyfile.name = re.search('<h1>(.*?)<br/></h1>', self.html).group(1)
        
        if self.account and self.premium:
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

        wait = self.load(self.pyfile.url, post={"downloadLink":"wait"})
        wait = wait.decode("UTF-8").encode("ascii", "ignore") # Remove unicode stuff
        self.setWait(int(wait)+3)
        self.wait()

        # show download link
        self.load(self.pyfile.url, post={"downloadLink":"show"})

        # this may either download our file or forward us to an error page
        dl = self.download(self.pyfile.url, post={"download":"normal"})

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
