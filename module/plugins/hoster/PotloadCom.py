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
    PATTERN_ID_FROM_URL = r'[a-z,A-Z,0-9]{1,}$'
    
    # http://potload.com/nfzxfl8gntaz => nfzxfl8gntaz
    PATTERN_HTML_FILENAME1 = r'<h3>.*\([0-9]*.*</h3>'
    PATTERN_HTML_FILENAME2 = r'>.* \('
    #<h3>test.zip (106 B)</h3>
    
    
    def process(self, pyfile):
		print "#" + pyfile.url + "#"
	#	ID = re.
	#	"[a-z,A-Z,0-9]{1,}$"
		
		# initial page
		print self.load(pyfile.url)
		
		# page where we have to wait (and get ids, ...)
		secondpage = self.load(pyfile.url, post={"op": "download1", "usr_login": "", "id": re.search(self.PATTERN_ID_FROM_URL, pyfile.url).group(0),
			"fname":"test.zip", "referer":pyfile.url},
			cookies=True)
		
		print secondpage
		
		ret = re.search(r'<Form method="POST".*</Form>', secondpage, flags=re.IGNORECASE | re.DOTALL)
		form = ret.group(0)
		print "#############################################"
		print "#############################################"
		print "#############################################"
		print form
		self.setWait(self.WAIT_TIME_SEC)
		
		# page where we get the final link
		
		

