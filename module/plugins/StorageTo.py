#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time

from Plugin import Plugin

class StorageTo(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "StorageTo"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www)?\.storage\.to/get/.*"
        props['version'] = "0.1"
        props['description'] = """Storage.to Download Plugin"""
        props['author_name'] = ("mkaay")
        props['author_mail'] = ("mkaay@mkaay.de")
        self.props = props
        self.parent = parent
        self.time_plus_wait = None
        self.want_reconnect = False
        self.api_data = None
        self.html = None
        self.read_config()
        self.multi_dl = False

        self.start_dl = False

    def prepare(self, thread):
        pyfile = self.parent
        
        self.req.clear_cookies()

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
        url = self.parent.url
        self.html = self.req.load(url, cookies=True)

    def download_api_data(self):
        url = self.parent.url
        info_url = url.replace("/get/", "/getlink/")
        src = self.req.load(info_url, cookies=True)
        pattern = re.compile(r"'(\w+)' : (.*?)[,|\}]")
        self.api_data = {}
        for pair in pattern.findall(src):
            self.api_data[pair[0]] = pair[1].strip("'")
        print self.api_data

    def get_wait_time(self):
        if not self.api_data:
            self.download_api_data()
        if self.api_data["state"] == "wait":
            self.want_reconnect = True
        self.time_plus_wait = time() + int(self.api_data["countdown"])
            
            

    def file_exists(self):
        """ returns True or False
        """
        if not self.api_data:
            self.download_api_data()
        if self.api_data["state"] == "failed":
            return False
        else:
            return True

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if not self.api_data:
            self.download_api_data()
        return self.api_data["link"]

    def get_file_name(self):
        if not self.html:
            self.download_html()
        file_name_pattern = r"<span class=\"orange\">Downloading:</span>(.*?)<span class=\"light\">(.*?)</span>"
        return re.search(file_name_pattern, self.html).group(1)

    def proceed(self, url, location):
        self.req.download(url, location, cookies=True)
