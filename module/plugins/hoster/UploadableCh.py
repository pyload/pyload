# -*- coding: utf-8 -*-
#Testlink:
#http://www.uploadable.ch/file/JG3nbN6fUCvh/test.txt
#
import re,time
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo
from module.plugins.ReCaptcha import ReCaptcha

class UploadableCh(SimpleHoster):
    __name__ = "UploadableCh"
    __type__ = "hoster"
    __pattern__ = r"https?://www.uploadable.ch/file/.*"
    __version__ = "0.01"
    __description__ = """uploadable.ch hoster plugin"""
    __author_name__ = ("zapp-brannigan")
    __author_mail__ = ("fuerst.reinje@web.de")
    
    FILE_INFO_PATTERN = r"""div id=\"file_name\" title=.*>(?P<N>.+)<span class=\"filename_normal\">\((?P<S>.*) (?P<U>[kKmMgG]?i?[bB].*)\)</span><"""
    RECAPTCHA_KEY = "6LdlJuwSAAAAAPJbPIoUhyqOJd7-yrah5Nhim5S3"
    WAIT_PATTERN = r'data-time=\"(\d+)\" data-format'
    FILE_ID = r'name=\"recaptcha_shortencode_field\" value=\"(.+)\"'
    FILE_OFFLINE_PATTERN = r'<h1>File not available</h1>'
  
    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1
        
    def process(self, pyfile):
        #Load website and set a cookie
        self.html = self.load(pyfile.url, cookies=True, decode=True)
        
        # Set some vars
        base_url = "http://www.uploadable.ch"
        file_id = re.search(self.FILE_ID,self.html).group(1)
        long_url = base_url+"/file/"+file_id+"/"+self.pyfile.name
        not_so_long_url = base_url+"/file/"+file_id
        self.logDebug("filename: "+pyfile.name)
        self.logDebug("base_url: "+base_url)
        self.logDebug("file_id: "+file_id)
        self.logDebug("long_url: "+long_url)
        self.logDebug("not_so_long_url: "+not_so_long_url)
              
        # Click the "free user" button and wait
        post_data = { "downloadLink": "wait" }
        a = self.load(not_so_long_url, cookies=True, post=post_data, decode=True)
        self.logDebug(a) #Expected output: {"waitTime":30}
        seconds = re.search(self.WAIT_PATTERN,self.html).group(1)
        self.setWait(int(seconds) + 2)
        self.wait()
        
        # Make the recaptcha appear and show it the pyload interface
        post_data = { "checkDownload": "check" }
        b = self.load(long_url, cookies=True, post=post_data, decode=True)
        self.logDebug(b) #Expected output: {"success":"showCaptcha"}
        recaptcha = ReCaptcha(self)
        challenge, code = recaptcha.challenge(self.RECAPTCHA_KEY)
        
        # Submit the captcha solution
        post_data = {"recaptcha_challenge_field": challenge, "recaptcha_response_field": code, "recaptcha_shortencode_field": file_id}
        self.load(base_url+"/checkReCaptcha.php", cookies=True, post=post_data, decode=True)
        time.sleep(3)
        
        # Get ready for downloading
        post_data = {"downloadLink": "show"}
        self.load(not_so_long_url, cookies=True, post=post_data, decode=True)
        time.sleep(3)
        
        # Download the file
        post_data = {"download": "normal"}
        self.download(not_so_long_url, cookies=True, post=post_data, disposition=True)
        
        # Check the downloaded file
        check = self.checkDownload({"wait_or_reconnect": re.compile("Please wait for"), "is_html": re.compile("<head>")})
        if check == "wait_or_reconnect":
            self.logInfo("Downloadlimit reached, please wait or reconnect")
            self.setWait(60*60,True)
            self.wait()
            self.retry()
        elif check == "is_html":
            self.logInfo("The downloaded file is html, maybe you entered a wrong captcha")
            self.retry()
        
getInfo = create_getInfo(UploadableCh)
