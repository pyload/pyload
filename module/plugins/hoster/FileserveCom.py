# -*- coding: utf-8 -*-
from __future__ import with_statement

import re

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.network.RequestFactory import getURL

try:
    from json import loads as json_loads
except ImportError: # pragma: no cover
    from module.lib.simplejson import loads as json_loads

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
    __version__ = "0.4"
    __description__ = """Fileserve.Com File Download Hoster"""
    __author_name__ = ("jeix", "mkaay", "paul king")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de", "")
    
    FILE_ID_KEY = r"fileserve\.com/file/(?P<id>\w+)"
    FILE_CHECK_KEY = r"<td>http://www.fileserve.com/file/(?P<id>\w+)</td>.*?<td>(?P<name>.*?)</td>.*?<td>(?P<units>.*?) (?P<scale>.B)</td>.*?<td>(?P<online>.*?)</td>"
    CAPTCHA_KEY_PATTERN = r"var reCAPTCHA_publickey='(?P<key>.*?)';"
    LONG_WAIT_PATTERN = r"You need to wait (\d+) seconds to start another download"
 
    def init(self):
        self.multiDL = False
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]
            if not self.premium:
                self.resumeDownload = False
                self.chunkLimit = 1

    def process(self, pyfile):
        self.checkFile()
        if self.account and self.premium:
            self.handlePremium()
        else:
            self.handleFree()
        
    def checkFile(self):
        self.file_id = re.search(self.FILE_ID_KEY, self.pyfile.url).group("id")
        self.logDebug("file id is %s" % self.file_id)
        
        self.pyfile.url = "http://www.fileserve.com/file/" + self.file_id
        
        linkCheck = self.load("http://www.fileserve.com/link-checker.php",
                               post = { "urls" : self.pyfile.url},
                               ref=False, cookies=False if self.account else True, decode=True)
                               
        linkMatch = re.search(self.FILE_CHECK_KEY, linkCheck.replace("\r\n",""))
        if not linkMatch:
	    self.logDebug("couldn't extract file status")
	    self.offline()
	
	if linkMatch.group("online").find("Available") != 0:
	    self.logDebug("file is not available : %s" % linkMatch.group("online"))
	    self.offline()
	  
	self.pyfile.name = linkMatch.group("name")

    
    def handlePremium(self):
        self.download(self.pyfile.url, post={"download":"premium"}, cookies=True)
    
    def handleFree(self):
        self.html = self.load(self.pyfile.url)
        action = self.load(self.pyfile.url, post={"checkDownload" : "check"}, decode=True)
        action = json_loads(action.replace(u"\ufeff",""))
        self.logDebug("action is : %s" % action)
        
        if "fail" in action:
            if action["fail"] == "timeLimit":
                html = self.load(self.pyfile.url, 
                                 post={"checkDownload" : "showError", 
                                       "errorType" : "timeLimit"},
                                 decode=True)
                wait = re.search(self.LONG_WAIT_PATTERN, html)
                if wait:
                    wait = int(wait.group(1))
                else:
                    wait = 720
                self.setWait(wait, True)
                self.wait()
                self.retry()
            else:
	        self.fail("Download check returned %s" % action["fail"])

        if action["success"] == "showCaptcha":
	    self.doCaptcha()
	    self.doTimmer()
	elif action["success"] == "showTimmer":
	    self.doTimmer()

        # show download link
        response = self.load(self.pyfile.url, post={"downloadLink":"show"}, decode=True)
        self.logDebug("show downloadLink response : %s" % response)
        if response.find("fail") == 0:
	    self.fail("Couldn't retrieve download url")

        # this may either download our file or forward us to an error page
        dl = self.download(self.pyfile.url, post={"download":"normal"})

        check = self.checkDownload({"expired": "Your download link has expired",
                                    "wait": re.compile(self.LONG_WAIT_PATTERN)})

        if check == "expired":
	    self.logDebug("Download link was expired")
            self.retry()
        elif check == "wait":
            wait_time = 720
            if self.lastCheck is not None:
                wait_time = int(self.lastCheck.group(1))
            self.setWait(wait_time+3, True)
            self.wait()
            self.retry()
            
        self.thread.m.reconnecting.wait(3) # Ease issue with later downloads appearing to be in parallel
            
    def doTimmer(self):
        wait = self.load(self.pyfile.url, 
                         post={"downloadLink" : "wait"},
                         decode=True).replace(u"\ufeff","") # remove UTF8 BOM
        self.logDebug("wait response : %s" % wait)
        
        if wait.find("fail") == 0:
	    self.fail("Failed getting wait time")
	    
        self.setWait(int(wait)) # remove UTF8 BOM
        self.wait()
      
    def doCaptcha(self):
        
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group("key")
        recaptcha = ReCaptcha(self)
        
        for i in range(5):
            challenge, code = recaptcha.challenge(captcha_key)
            
            response = json_loads(self.load("http://www.fileserve.com/checkReCaptcha.php", 
                                            post={'recaptcha_challenge_field' : challenge,
                                            'recaptcha_response_field' : code, 
                                            'recaptcha_shortencode_field' : self.file_id}).replace(u"\ufeff",""))
            self.logDebug("reCaptcha response : %s" % response)                                        
            if not response["success"]:
                 self.invalidCaptcha()
            else:
	         self.correctCaptcha()
	         break
     
