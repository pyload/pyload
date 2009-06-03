#!/usr/bin/env python

import re
from Plugin import Plugin

class XupIn(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "Dummy"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www.)?dummy.com/"
        props['version'] = "0.1"
        props['description'] = """Dummy Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = props
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.posts = {}
        self.want_reconnect = None
        self.multi_dl = False
    
    def set_parent_status(self):
        """ sets all available Statusinfos about a File in self.parent.status
        """
        if self.html == None:
            self.download_html()
        self.parent.status.filename = self.get_file_name()
        self.parent.status.url = self.get_file_url()
        self.parent.status.wait = self.wait_until()
        
    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect: 
            return file_url
        else:
            return False
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            return file_name
        else:
            return self.parent.url
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r"File nicht da", self.html, re.I) != None:
            return False
        else:
            return True

    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
