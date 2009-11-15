#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
from time import time
from module.Plugin import Plugin

class HotfileCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "HotfileCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://hotfile.com/dl/"
        props['version'] = "0.1"
        props['description'] = """Hotfile.com Download Plugin"""
        props['author_name'] = ("sitacuisses","spoob","mkaay")
        props['author_mail'] = ("sitacuisses@yhoo.de","spoob@pyload.org","mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.html = None
        self.want_reconnect = False
        self.multi_dl = False
        self.htmlwithlink = None
        self.url = None

    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False

        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            raise Exception, "The file was not found on the server."
            return False

        pyfile.status.filename = self.get_file_name()
            
        self.get_wait_time()
        pyfile.status.waituntil = self.time_plus_wait
        pyfile.status.want_reconnect = self.want_reconnect

        thread.wait(self.parent)
        
        pyfile.status.url = self.get_file_url()

        return True

    def download_html(self):
        self.url = self.parent.url
        self.html = self.req.load(self.url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            self.get_download_page()
            file_url = re.search("a href=\"(http://hotfile\.com/get/\S*?)\"", self.htmlwithlink).group(1)
            return file_url
        else:
            return False

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search('Downloading\s<b>(.*?)</b>', self.html).group(1)
            return file_name
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"Such file does not exist or it has been removed for infringement of copyrights.", self.html) != None:
            return False
        else:
            return True
    
    def get_wait_time(self):
        free_limit_pattern = re.compile(r"timerend=d\.getTime\(\)\+(\d+);")
        matches = free_limit_pattern.findall(self.html)
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

    def get_download_page(self):
        herewego = re.search(r"<form style=.*(\n<.*>\s*)*?\n<tr>", self.html).group(0)
        all_the_tuples = re.findall(r"<input\stype=hidden\sname=(\S*)\svalue=(\S*)>", herewego)
        
        self.htmlwithlink = self.req.load(self.url, None, all_the_tuples)

    def proceed(self, url, location):

        self.req.download(url, location)

