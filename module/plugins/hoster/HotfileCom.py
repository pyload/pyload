#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time
from module.plugins.Hoster import Hoster

class HotfileCom(Hoster):
    __name__ = "HotfileCom"
    __type__ = "hoster"
    __pattern__ = r"http://hotfile.com/dl/"
    __version__ = "0.2"
    __description__ = """Hotfile.com Download Hoster"""
    __author_name__ = ("sitacuisses","spoob","mkaay")
    __author_mail__ = ("sitacuisses@yhoo.de","spoob@pyload.org","mkaay@mkaay.de")

    def setup(self):
        self.html = [None, None]
        self.wantReconnect = False
        self.multiDL = False
        self.htmlwithlink = None
        self.url = None
        
        # if self.config['premium']:
            # self.multiDL = True
            # self.req.canContinue = True
        
    def process(self, pyfile):
        self.pyfile = pyfile        
        self.prepare()
        self.download( self.get_file_url() )

        
    def prepare(self):
        pyfile = self.pyfile
        self.wantReconnect = False
        
        self.download_html()

        if not self.file_exists():
            self.offline()

        pyfile.name = self.get_file_name()

        # if self.config['premium']:
            # pyfile.status.url = self.get_file_url()
            # return True
            
        self.setWait( self.get_wait_time() )
        self.wait()

        return True

    def download_html(self):
        # if self.config['premium']:
            # self.req.add_auth(self.config['username'], self.config['password'])
        self.html[0] = self.load(self.parent.url, get={"lang":"en"}, cookies=True)

    def get_file_url(self):
        # if self.config['premium']:
            # file_url_pattern = r'<td><a href="(http://hotfile.com/get/.+?)" class="click_download">'
            # file_url = re.search(file_url_pattern, self.html[0]).group(1)
        # else:
        
        form_content = re.search(r"<form style=.*(\n<.*>\s*)*?\n<tr>", self.html[0]).group(0)
        form_posts = re.findall(r"<input\stype=hidden\sname=(\S*)\svalue=(\S*)>", form_content)
        
        self.html[1] = self.load(self.parent.url, post=form_posts, cookies=True)
        
        file_url = re.search("a href=\"(http://hotfile\.com/get/\S*?)\"", self.html[1]).group(1)
        return file_url

    def get_file_name(self):
        file_name = re.search(r':</strong> (.+?) <span>\|</span>', self.html[0]).group(1)
        return file_name

    def file_exists(self):
        if re.search(r"404 - Not Found", self.html[0]) != None or self.html[0] == "":
            return False
        return True
    
    def get_wait_time(self):
        free_limit_pattern = re.compile(r"timerend=d\.getTime\(\)\+(\d+);")
        matches = free_limit_pattern.findall(self.html[0])
        if matches:
            for match in matches:
                if int(match) == 60000:
                    continue
                if int(match) == 0:
                    continue
                else:
                    self.wantReconnect = True
                    return int(match)/1000 + 65
            return 65
