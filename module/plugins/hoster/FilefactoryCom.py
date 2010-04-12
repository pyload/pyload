#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.Plugin import Plugin
from time import time

class FilefactoryCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "FilefactoryCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www\.)?filefactory\.com/file/"
        props['version'] = "0.1"
        props['description'] = """Filefactory.com Download Plugin"""
        props['author_name'] = ("sitacuisses","spoob","mkaay")
        props['author_mail'] = ("sitacuisses@yahoo.de","spoob@pyload.org","mkaay@mkaay.de")
        self.props = props
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
        self.html = self.req.load(url, cookies=True)
        tempurl = re.search('a href=\"(.*?)\".*?button\.basic\.jpg', self.html).group(1)
        self.htmlwithlink = self.req.load("http://www.filefactory.com"+tempurl, cookies=True)

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

        self.req.download(url, location, cookies=True)

