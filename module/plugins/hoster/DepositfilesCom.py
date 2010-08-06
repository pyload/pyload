#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from module.plugins.Hoster import Hoster

class DepositfilesCom(Hoster):
    __name__ = "DepositfilesCom"
    __type__ = "hoster"
    __pattern__ = r"http://depositfiles.com/.{2,}/files/"
    __version__ = "0.1"
    __description__ = """Depositfiles.com Download Hoster"""
    __author_name__ = ("spoob")
    __author_mail__ = ("spoob@pyload.org")

    def setup(self):
        self.multiDL = False
        
    def process(self, pyfile):
        self.pyfile = pyfile
        self.prepare()            
        pyfile.name = self.get_file_name()
        self.download(self.get_file_url())

    def prepare(self):
        self.html = self.load(self.pyfile.url)
        if re.search(r'File is checked, please try again in a minute.', self.html) != None:
            self.log.info("DepositFiles.com: The file is being checked. Waiting 1 minute.")
            self.setWait(61)
            self.wait()
            
        if re.search(r'Such file does not exist or it has been removed for infringement of copyrights', self.html) != None:
            self.offline()
            
        self.html = self.load(self.pyfile.url, post={"gateway_result":"1"})
        wait_time = int(re.search(r'<span id="download_waiter_remain">(.*?)</span>', self.html).group(1))
        self.setWait(wait_time)
        self.log.debug("DepositFiles.com: Waiting %d seconds." % wait_time)
        
    def get_file_url(self):
        return urllib.unquote(re.search('<form action="(http://.+?\.depositfiles.com/.+?)" method="get"', self.html).group(1))

    def get_file_name(self):
        return re.search('File name: <b title="(.*)">', self.html).group(1)

    def file_exists(self):
        self.html = self.load(self.parent.url)
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights", self.html) != None:
            return False
        return True
