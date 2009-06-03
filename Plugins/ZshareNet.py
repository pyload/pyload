#!/usr/bin/env python

import re
from Plugin import Plugin

class ZshareNet(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "ZshareNet"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www.)?zshare.net/"
        props['version'] = "0.1"
        props['description'] = """Zshare.net Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = props
        self.parent = parent
        self.html = [None, None]
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.posts = {}
        self.want_reconnect = None
        self.multi_dl = False
    
    def set_parent_status(self):
        """ sets all available Statusinfos about a File in self.parent.status
        """
        if self.html[0] == None:
            self.download_html()
        self.parent.status.filename = self.get_file_name()
        self.parent.status.url = self.get_file_url()
        self.parent.status.wait = self.wait_until()
        
    def download_html(self):
        url = self.parent.url
        self.html[0] = self.req.load(url)
        if "/video/" in url:
            url = url.replace("/video/", "/download/")
        elif "/audio/" in url:
            url = url.replace("/audio/", "/download/")
        elif "/image/" in url:
            url = url.replace("/image/", "/download/")
        self.html[1] = self.req.load(url, None, {"download": "1"})
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_url = "".join(eval(re.search("var link_enc=new Array(.*);link", self.html[1]).group(1)))
            return file_url
        else:
            return False
        
    def get_file_name(self):
        if self.html[0] == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search("<font color=\"#666666\">(.*)</font></td>", self.html[0]).group(1)
            print file_name
            return file_name
        else:
            return self.parent.url
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html[0] == None:
            self.download_html()
        if re.search(r"File Not Found", self.html[0]) != None:
            return False
        else:
            return True

    def wait_until(self):
        if self.html[0] == None:
            self.download_html()
        return self.time_plus_wait
