#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster
from time import time

class FilefactoryCom(Hoster):
    __name__ = "FilefactoryCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?filefactory\.com/file/"
    __version__ = "0.1"
    __description__ = """Filefactory.com Download Hoster"""
    __author_name__ = ("sitacuisses","spoob","mkaay")
    __author_mail__ = ("sitacuisses@yahoo.de","spoob@pyload.org","mkaay@mkaay.de")

    def __init__(self, parent):
        Hoster.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.want_reconnect = False
        self.multi_dl = False
        self.htmlwithlink = None
    
    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False
        
        self.download_html()
        
        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            return False
            
        self.get_waiting_time()

        pyfile.status.filename = self.get_file_name()
            
        pyfile.status.waituntil = self.time_plus_wait
        pyfile.status.url = self.get_file_url()
        pyfile.status.want_reconnect = self.want_reconnect

        thread.wait(self.parent)

        return True

    def download_html(self):
        url = self.parent.url
        self.html = self.load(url, cookies=True)
        tempurl = re.search('a href=\"(.*?)\".*?button\.basic\.jpg', self.html).group(1)
        self.htmlwithlink = self.load("http://www.filefactory.com"+tempurl, cookies=True)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_url = re.search('a href=\"(.*?)\" id=\"downloadLinkTarget\"', self.htmlwithlink).group(1)
            #print file_url
            return file_url
        else:
            return False

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search('content=\"Download\ (\S*?)\ for\ free\.', self.html).group(1)
            return file_name
        else:
            return self.parent.url
    
    def get_waiting_time(self):
        if self.html == None:
            self.download_html()
        countdown_re = re.compile("countdown.*?>(\d+)")
        m = countdown_re.search(self.htmlwithlink)
        if m:
            sec = int(m.group(1))
        else:
            sec = 0
        self.time_plus_wait = time() + sec

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights.", self.html) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.download(url, location, cookies=True)

