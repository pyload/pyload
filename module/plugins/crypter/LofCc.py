#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import sleep
from os.path import join

from module.plugins.Crypter import Crypter
from module.plugins.ReCaptcha import ReCaptcha

class LofCc(Crypter):
    __name__ = "LofCc"
    __type__ = "container"
    __pattern__ = r"http://lof.cc/(.*)"
    __version__ = "0.1"
    __description__ = """lof.cc Plugin"""
    __author_name__ = ("mkaay")
    __author_mail__ = ("mkaay@mkaay.de")

    def setup(self):
        self.multiDL = False
    
    def decrypt(self, pyfile):
        html = self.req.load(self.pyfile.url, cookies=True)
        
        m = re.search(r"src=\"http://www.google.com/recaptcha/api/challenge\?k=(.*?)\"></script>", html)
        if not m:
            self.offline()
        
        recaptcha = ReCaptcha(self)
        challenge, code = recaptcha.challenge(m.group(1))
        
        resultHTML = self.req.load(self.pyfile.url, post={"recaptcha_challenge_field":challenge, "recaptcha_response_field":code}, cookies=True)
        
        if re.search("class=\"error\"", resultHTML):
            self.retry()
        
        self.correctCaptcha()
        
        dlc = self.req.load(self.pyfile.url+"/dlc", cookies=True)
        
        name = re.search(self.__pattern__, self.pyfile.url).group(1)+".dlc"
        
        dlcFile = join(self.config["general"]["download_folder"], name)
        f = open(dlcFile, "wb")
        f.write(dlc)
        f.close()
        
        self.packages.append((self.pyfile.package().name, [dlcFile], self.pyfile.package().folder))
