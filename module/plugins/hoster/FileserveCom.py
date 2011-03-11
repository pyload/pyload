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
    __pattern__ = r"http://(www\.)?fileserve\.com/file/[a-zA-Z0-9]+"
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

        self.file_id = re.search(r"fileserve\.com/file/([a-zA-Z0-9]+)(http:.*)?", self.pyfile.url).group(1)

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

        self.html = self.load(self.pyfile.url)
        jsPage = re.search(r"\"(/landing/.*?/download_captcha\.js)\"", self.html)
        self.req.putHeader("X-Requested-With", "XMLHttpRequest")

        jsPage = self.load("http://fileserve.com" + jsPage.group(1))
        action = self.load(self.pyfile.url, post={"checkDownload" : "check"})

        if "timeLimit" in action:
            html = self.load(self.pyfile.url, post={"checkDownload" : "showError", "errorType" : "timeLimit"})
            wait = re.search(r"You need to wait (\d+) seconds to start another download", html)
            if wait:
                wait = int(wait.group(1))
            else:
                wait = 720

            self.setWait(wait, True)
            self.wait()
            self.retry()

        if r'<div id="captchaArea" style="display:none;">' in self.html or \
           r'/showCaptcha\(\);' in self.html:
            # we got a captcha
            id = re.search(r"var reCAPTCHA_publickey='(.*?)';", self.html).group(1)
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            
            self.html = self.load(r'http://www.fileserve.com/checkReCaptcha.php', post={'recaptcha_challenge_field':challenge,
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
                self.setWait(30)
            else:
                self.setWait(int(wait))

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
