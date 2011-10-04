# -*- coding: utf-8 -*-
from __future__ import with_statement

from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

import re

def getInfo(urls):
    result = []
    
    for url in urls:
        
        # Get file info html
        # @TODO: Force responses in english language so current patterns will be right
        html = getURL(url)
        if re.search(FilefactoryCom.FILE_OFFLINE_PATTERN, html):
            result.append((url, 0, 1, url))

        # Name
        name = re.search(FilefactoryCom.FILE_NAME_PATTERN, html).group('name')
        m = re.search(FilefactoryCom.FILE_INFO_PATTERN, html)
        
        # Size
        value = float(m.group('size'))
        units = m.group('units')
        pow = {'KB' : 1, 'MB' : 2, 'GB' : 3}[units] 
        size = int(value*1024**pow)
    
        # Return info
        result.append((name, size, 2, url))
        
    yield result
    
class FilefactoryCom(Hoster):
    __name__ = "FilefactoryCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?filefactory\.com/file/(?P<id>[a-zA-Z0-9]+)" # URLs given out are often longer but this is the requirement
    __version__ = "0.3"
    __description__ = """Filefactory.Com File Download Hoster"""
    __author_name__ = ("paulking")
    
    FILE_OFFLINE_PATTERN = r'<title>File Not Found'
    FILE_NAME_PATTERN = r'<span class="last">(?P<name>.*?)</span>'
    FILE_INFO_PATTERN = r'<span>(?P<size>\d(\d|\.)*) (?P<units>..) file uploaded'
    FILE_CHECK_PATTERN = r'check:\'(?P<check>.*?)\''
    CAPTCHA_KEY_PATTERN = r'Recaptcha.create\("(?P<recaptchakey>.*?)",' 
    WAIT_PATH_PATTERN = r'path:"(?P<path>.*?)"'
    WAIT_PATTERN = r'id="startWait" value="(?P<wait>\d+)"'
    FILE_URL_PATTERN = r'<a href="(?P<url>.*?)" id="downloadLinkTarget">'
        
    def setup(self):
        self.multiDL = False

    def process(self, pyfile):
    
        self.pyfile = pyfile
        
        # Force responses language to US English
        self.req.cj.setCookie("filefactory.com", "ff_locale","")

        # Load main page
        self.html = self.load(self.pyfile.url, ref=False, decode=True)

        # Check offline
        if re.search(self.FILE_OFFLINE_PATTERN, self.html) is not None:
            self.offline()
        
        # File id
        self.file_id = re.match(self.__pattern__, self.pyfile.url).group('id')
        self.log.debug("%s: File id is [%s]" % (self.__name__, self.file_id))
           
        # File name
        self.pyfile.name = re.search(self.FILE_NAME_PATTERN, self.html).group('name')

        # Check Id
        self.check = re.search(self.FILE_CHECK_PATTERN, self.html).group('check')
        self.log.debug("%s: File check code is [%s]" % (self.__name__, self.check))

        # Handle free downloading
        self.handleFree()
    
    def handleFree(self):
    
        # Resolve captcha
        self.log.debug("%s: File is captcha protected" % self.__name__)
        id = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group('recaptchakey')
        # Try up to 5 times
        for i in range(5):
            self.log.debug("%s: Resolving ReCaptcha with key [%s], round %d" % (self.__name__, id, i+1))
            recaptcha = ReCaptcha(self)
            challenge, code = recaptcha.challenge(id)
            response = self.load("http://www.filefactory.com/file/checkCaptcha.php",
                            post={"check" : self.check, "recaptcha_challenge_field" : challenge, "recaptcha_response_field" : code})
            captchavalid = self.handleCaptchaErrors(response)
            if captchavalid:
                break
        if not captchavalid:
            self.fail("No valid captcha after 5 attempts")

        # Get wait URL
        waitpath = re.search(self.WAIT_PATH_PATTERN, response).group('path')
        waiturl = "http://www.filefactory.com" + waitpath
        
        # This will take us to a wait screen
        self.log.debug("%s: fetching wait with url [%s]" % (self.__name__, waiturl))
        waithtml = self.load(waiturl, decode=True)

        # Find the wait value and wait     
        wait = int(re.search(self.WAIT_PATTERN, waithtml).group('wait'))
        self.log.debug("%s: Waiting %d seconds." % (self.__name__, wait))
        self.setWait(wait, True)
        self.wait()

        # Now get the real download url and retrieve the file
        url = re.search(self.FILE_URL_PATTERN,waithtml).group('url')
        # this may either download our file or forward us to an error page
        self.log.debug("%s: download url %s" % (self.__name__, url))
        dl = self.download(url)
        
        check = self.checkDownload({"multiple": "You are currently downloading too many files at once.",
                                    "error": '<div id="errorMessage">'})

        if check == "multiple":
            self.setWait(15*60)
            self.log.debug("%s: Parallel downloads detected waiting 15 minutes" % self.__name__)
            self.wait()
            self.retry()
        elif check == "error":
            self.fail("Unknown error")

    def handleCaptchaErrors(self, response):
        self.log.debug("%s: Result of captcha resolving [%s]" % (self.__name__, response))
        if 'status:"ok"' in response:
            self.correctCaptcha()
            return True
        
        self.log.debug("%s: Wrong captcha" % self.__name__)
        self.invalidCaptcha()
