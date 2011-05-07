# -*- coding: utf-8 -*-
from __future__ import with_statement

import re

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
    __version__ = "0.3"
    __description__ = """Bitshare.Com File Download Hoster"""
    __author_name__ = ("paul", "king", "fragonib")
    __author_mail__ = ("", "", "fragonib[AT]yahoo[DOT]es")
    
    HOSTER_DOMAIN = "bitshare.com"
    FILE_OFFLINE_PATTERN = r'''(>We are sorry, but the requested file was not found in our database|>Error - File not available<|The file was deleted either by the uploader, inactivity or due to copyright claim)'''
    FILE_INFO_PATTERN = r'<h1>Downloading\s(?P<name>.+?)\s-\s(?P<size>\d+)\s(?P<units>..)yte</h1>'
    FILE_AJAXID_PATTERN = r'var ajaxdl = "(.*?)";'
    CAPTCHA_KEY_PATTERN = r"http://api\.recaptcha\.net/challenge\?k=(.*?) " 
        
    def setup(self):
        self.multiDL = False
        self.chunkLimit = 1

    def process(self, pyfile):
    
        self.pyfile = pyfile
        
        # File id
        m = re.match(self.__pattern__, self.pyfile.url)
        self.file_id = max(m.group('id1'), m.group('id2')) 
        self.log.debug("%s: File id is [%s]" % (self.__name__, self.file_id))

        # Load main page
        self.req.cj.setCookie(self.HOSTER_DOMAIN, "language_selection", "EN")
        self.html = self.load(self.pyfile.url, ref=False, utf8=True, cookies=True)

        # Check offline
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()
           
        # File name
        name1 = re.search(BitshareCom.__pattern__, self.pyfile.url).group('name')
        name2 = re.search(BitshareCom.FILE_INFO_PATTERN, self.html).group('name')
        self.pyfile.name = max(name1, name2)

        # Ajax file id
        self.ajaxid = re.search(BitshareCom.FILE_AJAXID_PATTERN, self.html).group(1)
        self.log.debug("%s: File ajax id is [%s]" % (self.__name__, self.ajaxid))

        # Handle free downloading
        self.handleFree()
    
    def handleFree(self):

        # Get download info
        self.log.debug("%s: Getting download info" % self.__name__)
        response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                            post={"request" : "generateID", "ajaxid" : self.ajaxid})
        self.handleErrors(response, ':')
        parts = response.split(":")
        filetype = parts[0]
        wait = int(parts[1])
        captcha = int(parts[2])
        self.log.debug("%s: Download info [type: '%s', waiting: %d, captcha: %d]" % 
                       (self.__name__, filetype, wait, captcha))

        # Waiting
        if wait > 0:
            self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait))
            self.setWait(wait, True)
            self.wait()
            
        # Resolve captcha
        if captcha == 1:
            self.log.debug("%s: File is captcha protected" % self.__name__)
            id = re.search(BitshareCom.CAPTCHA_KEY_PATTERN, self.html).group(1)
            # Try up to 3 times
            for i in range(3):
                self.log.debug("%s: Resolving ReCaptcha with key [%s], round %d" % (self.__name__, id, i+1))
                recaptcha = ReCaptcha(self)
                challenge, code = recaptcha.challenge(id)
                response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                                post={"request" : "validateCaptcha", "ajaxid" : self.ajaxid, "recaptcha_challenge_field" : challenge, "recaptcha_response_field" : code})
                if self.handleCaptchaErrors(response):
                    break


        # Get download URL
        self.log.debug("%s: Getting download url" % self.__name__)
        response = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                    post={"request" : "getDownloadURL", "ajaxid" : self.ajaxid})
        self.handleErrors(response, '#')
        url = response.split("#")[-1]    

        # Request download URL
        # This may either download our file or forward us to an error page
        self.log.debug("%s: Downloading file with url [%s]" % (self.__name__, url))
        self.download(url)
        
    def handleErrors(self, response, separator):
        self.log.debug("%s: Checking response [%s]" % (self.__name__, response))
        if "ERROR" in response:
            msg = response.split(separator)[-1]
            self.fail(msg)

    def handleCaptchaErrors(self, response):
        self.log.debug("%s: Result of captcha resolving [%s]" % (self.__name__, response))
        if "SUCCESS" in response:
            self.correctCaptcha()
            return True
        self.log.debug("%s: Wrong captcha" % self.__name__)
        self.invalidCaptcha()