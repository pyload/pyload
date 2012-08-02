# -*- coding: utf-8 -*-
from __future__ import with_statement

import re
from pycurl import FOLLOWLOCATION

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha
from module.network.RequestFactory import getRequest


def getInfo(urls):
    result = []
    
    for url in urls:
        
        # Get file info html
        req = getRequest()
        req.cj.setCookie(BitshareCom.HOSTER_DOMAIN, "language_selection", "EN")
        html = req.load(url)
        req.close()
        
        # Check online        
        if re.search(BitshareCom.FILE_OFFLINE_PATTERN, html):
            result.append((url, 0, 1, url))
            continue

        # Name
        name1 = re.search(BitshareCom.__pattern__, url).group('name')
        m = re.search(BitshareCom.FILE_INFO_PATTERN, html)
        name2 = m.group('name')
        name = max(name1, name2)
        
        # Size
        value = float(m.group('size'))
        units = m.group('units')
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[units] 
        size = int(value*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result

class BitshareCom(Hoster):
    __name__ = "BitshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?bitshare\.com/(files/(?P<id1>[a-zA-Z0-9]+)(/(?P<name>.*?)\.html)?|\?f=(?P<id2>[a-zA-Z0-9]+))"
    __version__ = "0.45"
    __description__ = """Bitshare.Com File Download Hoster"""
    __author_name__ = ("paulking", "fragonib")
    __author_mail__ = (None, "fragonib[AT]yahoo[DOT]es")
    
    HOSTER_DOMAIN = "bitshare.com"
    FILE_OFFLINE_PATTERN = r'''(>We are sorry, but the requested file was not found in our database|>Error - File not available<|The file was deleted either by the uploader, inactivity or due to copyright claim)'''
    FILE_INFO_PATTERN = r'<h1>(Downloading|Streaming)\s(?P<name>.+?)\s-\s(?P<size>[\d.]+)\s(?P<units>..)yte</h1>'
    FILE_AJAXID_PATTERN = r'var ajaxdl = "(.*?)";'
    CAPTCHA_KEY_PATTERN = r"http://api\.recaptcha\.net/challenge\?k=(.*?) " 
        
    def setup(self):
        self.multiDL = self.premium
        self.chunkLimit = 1

    def process(self, pyfile):
        if self.premium:
            self.account.relogin(self.user)
    
        self.pyfile = pyfile
        
        # File id
        m = re.match(self.__pattern__, self.pyfile.url)
        self.file_id = max(m.group('id1'), m.group('id2')) 
        self.logDebug("File id is [%s]" % self.file_id)

        # Load main page
        self.req.cj.setCookie(self.HOSTER_DOMAIN, "language_selection", "EN")
        self.html = self.load(self.pyfile.url, ref=False, decode=True, cookies = False)

        # Check offline
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()
           
        # File name
        m = re.search(BitshareCom.__pattern__, self.pyfile.url)
        name1 = m.group('name') if m is not None else None
        m = re.search(BitshareCom.FILE_INFO_PATTERN, self.html)
        name2 = m.group('name') if m is not None else None
        self.pyfile.name = max(name1, name2)

        # Ajax file id
        self.ajaxid = re.search(BitshareCom.FILE_AJAXID_PATTERN, self.html).group(1)
        self.logDebug("File ajax id is [%s]" % self.ajaxid)
        
        # This may either download our file or forward us to an error page
        url = self.getDownloadUrl()        
        self.logDebug("Downloading file with url [%s]" % url)
        self.download(url)

        
    def getDownloadUrl(self):
        # Return location if direct download is active
        if self.premium:
            header = self.load(self.pyfile.url, cookies = True, just_header = True)
            if 'location' in header:
                return header['location']  
            
        # Get download info
        self.logDebug("Getting download info")
        response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                            post={"request" : "generateID", "ajaxid" : self.ajaxid})
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
                self.setWait(wait, False)
                self.wait()
            else:
                self.setWait(wait - 55, True)
                self.wait()
                self.retry()  
            
        # Resolve captcha
        if captcha == 1:
            self.logDebug("File is captcha protected")
            id = re.search(BitshareCom.CAPTCHA_KEY_PATTERN, self.html).group(1)
            # Try up to 3 times
            for i in range(3):
                self.logDebug("Resolving ReCaptcha with key [%s], round %d" % (id, i+1))
                recaptcha = ReCaptcha(self)
                challenge, code = recaptcha.challenge(id)
                response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                                post={"request" : "validateCaptcha", "ajaxid" : self.ajaxid, "recaptcha_challenge_field" : challenge, "recaptcha_response_field" : code})
                if self.handleCaptchaErrors(response):
                    break


        # Get download URL
        self.logDebug("Getting download url")
        response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                    post={"request" : "getDownloadURL", "ajaxid" : self.ajaxid})
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
