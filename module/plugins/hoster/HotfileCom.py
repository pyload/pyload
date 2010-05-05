#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time
from module.plugins.Hoster import Hoster

class HotfileCom(Hoster):
    __name__ = "HotfileCom"
    __type__ = "hoster"
    __pattern__ = r"http://hotfile.com/dl/"
    __version__ = "0.1"
    __description__ = """Hotfile.com Download Hoster"""
    __author_name__ = ("sitacuisses","spoob","mkaay")
    __author_mail__ = ("sitacuisses@yhoo.de","spoob@pyload.org","mkaay@mkaay.de")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = [None, None]
        self.want_reconnect = False
        self.multi_dl = False
        self.htmlwithlink = None
        self.url = None
        self.read_config()
        if self.config['premium']:
            self.multi_dl = True
            self.req.canContinue = True
        else:
            self.multi_dl = False
        
    def prepare(self, thread):
        pyfile = self.parent
        self.want_reconnect = False
        
        self.download_html()
        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            return False

        pyfile.status.filename = self.get_file_name()

        if self.config['premium']:
            pyfile.status.url = self.get_file_url()
            return True
            
        self.get_wait_time()
        pyfile.status.waituntil = self.time_plus_wait
        pyfile.status.want_reconnect = self.want_reconnect

        thread.wait(self.parent)
        
        pyfile.status.url = self.get_file_url()
        return True

    def download_html(self):
        if self.config['premium']:
            self.req.add_auth(self.config['username'], self.config['password'])
        self.url = self.parent.url
        self.html[0] = self.load(self.url, get={"lang":"en"}, cookies=True)

    def get_file_url(self):
        if self.config['premium']:
            file_url_pattern = r'<td><a href="(http://hotfile.com/get/.+?)" class="click_download">'
            file_url = re.search(file_url_pattern, self.html[0]).group(1)
        else:
            form_content = re.search(r"<form style=.*(\n<.*>\s*)*?\n<tr>", self.html[0]).group(0)
            form_posts = re.findall(r"<input\stype=hidden\sname=(\S*)\svalue=(\S*)>", form_content)
            self.html[1] = self.load(self.url, post=form_posts, cookies=True)
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
                    self.time_plus_wait = time() + int(match)/1000 + 65
                    self.want_reconnect = True
                    return True
            self.time_plus_wait = time() + 65
