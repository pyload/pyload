# -*- coding: utf-8 -*-

# Test links (test.zip):
# http://potload.com/nfzxfl8gntaz

import re
import subprocess
import tempfile
import os

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, timestamp
from module.plugins.internal.CaptchaService import ReCaptcha
from module.common.json_layer import json_loads


class PotloadCom(SimpleHoster):
    __name__ = "PotloadCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?potload\.com/[a-z,A-Z,0-9]*"
    __version__ = "0.01"
    __description__ = """Potload.com Download Hoster"""
    __author_name__ = ("duneyr")
    __author_mail__ = ("contact_me_at_github@nomail.com")
    __config__ = []
    
    WAIT_TIME_SEC = 22
    # http://potload.com/nfzxfl8gntaz => nfzxfl8gntaz
    PATTERN_ID_FROM_URL = r'[a-z,A-Z,0-9]{1,}$'
    
    PATTERN_HTML_FILENAME1 = r'<h3>.*\([0-9]*.*</h3>'
    PATTERN_HTML_FILENAME2 = r'>.* \('
    #<h3>test.zip (106 B)</h3> => >test.zip (
    
    PATTERN_HTML_TOKEN = r'rand" value="[a-z,0-9]*'
    
    PATTERN_HTML_TARGET_URL = r'downloadurl">[^/d]*<a href="[^"]*'
    
    def setup(self):
        self.multiDL = False
        
    def process(self, pyfile):
       
        # initial page
        firstpage=self.load(pyfile.url, cookies=True)
        
        # check for offline
        if not re.search("<h2>DOWNLOAD FILE:</h2>", firstpage, flags=re.IGNORECASE):
            self.offline()
            return	        
        
        #self.wantReconnect = True
        
        # get filename (for post data)
        ret = re.search(self.PATTERN_HTML_FILENAME1, firstpage, flags=re.IGNORECASE)
        form = ret.group(0)
        ret = re.search(self.PATTERN_HTML_FILENAME2, form, flags=re.IGNORECASE)
        extract = ret.group(0)
        filename = extract[1:-2]
        self.pyfile.name = filename

        

        
        # page where we have to wait (and submit first pkg of data)
        secondpage = self.load(pyfile.url, post={"op": "download1", "usr_login": "", "id": re.search(self.PATTERN_ID_FROM_URL, pyfile.url).group(0),
            "fname":filename, "referer":pyfile.url, "method_free":"Slow+Download"},
            cookies=True)
        
        
        # get token
        ret = re.search(self.PATTERN_HTML_TOKEN, secondpage, flags=re.IGNORECASE | re.DOTALL)
        token = ret.group(0)[13:]

		
        self.setWait(self.WAIT_TIME_SEC)
        self.logDebug("PotLoad: final wait %d seconds" % self.WAIT_TIME_SEC)
        self.wait()      
        
        # get page which provides link
        thirdpage = self.load(pyfile.url, post={"op": "download2", "usr_login": "", "id": re.search(self.PATTERN_ID_FROM_URL, pyfile.url).group(0),
            "fname":filename, "referer":pyfile.url, "method_free":"Slow+Download", "rand":token},
            cookies=True)
        
        # filter link
        ret = re.search(self.PATTERN_HTML_TARGET_URL, thirdpage, flags=re.IGNORECASE | re.DOTALL)
        link = ret.group(0)[25:]

        
        
        self.download(link, disposition=True)
		
		

