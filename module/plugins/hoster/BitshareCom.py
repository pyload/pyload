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
        if re.search(BitshareCom.OFFLINE_PATTERN, html):
            result.append((url, 0, 1, url))

        # Name
        name1 = re.search(BitshareCom.__pattern__, url).group('name')
        m = re.search(BitshareCom.FILE_INFO_PATTERN, html)
        name2 = m.group('name')
        name = unicode2str(max(name1, name2))
        
        # Size
        value = float(m.group('size'))
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[m.group('units')] 
        size = int(value*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result

class BitshareCom(Hoster):
    __name__ = "BitshareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?bitshare\.com/(files/(?P<id1>[a-zA-Z0-9]+)(/(?P<name>.*?)\.html)?|\?f=(?P<id2>[a-zA-Z0-9]+))"
    __version__ = "0.2"
    __description__ = """Bitshare.Com File Download Hoster"""
    __author_name__ = ("paul", "king")
    
    OFFLINE_PATTERN = r'''(>We are sorry, but the requested file was not found in our database|>Error - File not available<|The file was deleted either by the uploader, inactivity or due to copyright claim)'''
    FILE_INFO_PATTERN = r'<h1>.*\s(?P<name>.+?)\s-\s(?P<size>\d+)\s(?P<units>..)yte</h1>'
        
    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
    
        self.pyfile = pyfile
        self.req.cj.setCookie("bitshare.com", "language_selection", "EN")
    
        # File id
        m = re.match(self.__pattern__, self.pyfile.url)
        self.file_id = max(m.group('id1'), m.group('id2')) 

        # File url
        self.log.debug("%s: File_id is %s" % (self.__name__, self.file_id))

        # Load main page
        self.html = self.load(self.pyfile.url, ref=False, utf8=True, cookies=True)

        # Check offline
        if re.search(self.OFFLINE_PATTERN, self.html) is not None:
            self.offline()
           
        # File name
        name1 = re.search(BitshareCom.__pattern__, self.pyfile.url).group('name')
        name2 = re.search(BitshareCom.FILE_INFO_PATTERN, self.html).group('name')
        self.pyfile.name = unicode2str(max(name1, name2))

        self.ajaxid = re.search("var ajaxdl = \"(.*?)\";",self.html).group(1)
        
        self.log.debug("%s: AjaxId %s" % (self.__name__, self.ajaxid))

        self.handleFree()
    
    def handleFree(self):

        action = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                            post={"request" : "generateID", "ajaxid" : self.ajaxid})
        self.log.debug("%s: Result of generateID %s" % (self.__name__, action))
        parts = action.split(":")
    
        if parts[0] == "ERROR":
            self.fail(parts[1])
        
        filetype = parts[0]
        wait = int(parts[1])
        captcha = int(parts[2])

        if wait > 0:
            self.log.info("%s: Waiting %d seconds." % (self.__name__, wait))
            self.setWait(wait, True)
            self.wait()
            
        if captcha == 1:
            id = re.search(r"http://api\.recaptcha\.net/challenge\?k=(.*?) ", self.html).group(1)
            self.log.debug("%s: ReCaptcha key %s" % (self.__name__, id))
            for i in range(3):   # Try upto 3 times
                recaptcha = ReCaptcha(self)
                challenge, code = recaptcha.challenge(id)
                action = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                                post={"request" : "validateCaptcha", "ajaxid" : self.ajaxid, "recaptcha_challenge_field" : challenge, "recaptcha_response_field" : code})
                parts = action.split(":")
                if parts[0] != "SUCCESS":
                    self.invalidCaptcha()
                else:
                    break

        action = self.load("http://bitshare.com/files-ajax/" + self.file_id + "/request.html",
                    post={"request" : "getDownloadURL", "ajaxid" : self.ajaxid})

        parts = action.split("#")
    
        if parts[0] == "ERROR":
            self.fail(parts[1])

        # this may either download our file or forward us to an error page
        self.log.debug("%s: Download url %s" % (self.__name__, parts[1]))
        dl = self.download(parts[1])
