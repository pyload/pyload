#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class LixIn(Crypter):
    __name__ = "LixIn"
    __type__ = "container"
    __pattern__ = r"http://(www.)?lix.in/(?P<id>.*)"
    __version__ = "0.21"
    __description__ = """Lix.in Container Plugin"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")
    
    CAPTCHA_PATTERN='<img src="(?P<image>captcha_img.php\?PHPSESSID=.*?)"'
    SUBMIT_PATTERN=r"value='continue.*?'"
    LINK_PATTERN=r'name="ifram" src="(?P<link>.*?)"'
    

    def decrypt(self, pyfile):
        url = pyfile.url
        
        matches = re.search(self.__pattern__,url)
        if not matches:
            self.fail("couldn't identify file id")
            
        id = matches.group("id")
        self.logDebug("File id is %s" % id)
        
        self.html = self.req.load(url, decode=True)
        
        matches = re.search(self.SUBMIT_PATTERN,self.html)
        if not matches:
	    self.fail("link doesn't seem valid")

        matches = re.search(self.CAPTCHA_PATTERN, self.html)
        if matches:
            for i in range(5):
                matches = re.search(self.CAPTCHA_PATTERN, self.html)
                if matches:
                    self.logDebug("trying captcha")
                    captcharesult = self.decryptCaptcha("http://lix.in/"+matches.group("image"))
	            self.html = self.req.load(url, decode=True, post={"capt" : captcharesult, "submit":"submit","tiny":id})
	        else:
	            self.logDebug("no captcha/captcha solved")
	            break
    	else:
            self.html = self.req.load(url, decode=True, post={"submit" : "submit",
	                                                      "tiny"   : id})
	                                     
        matches = re.search(self.LINK_PATTERN, self.html)
        if not matches:
	    self.fail("can't find destination url")

        new_link = matches.group("link")
        self.logDebug("Found link %s, adding to package" % new_link)

        self.packages.append((self.pyfile.package().name, [new_link], self.pyfile.package().name))
           