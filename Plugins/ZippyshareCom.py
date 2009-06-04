#!/usr/bin/env python

import re
import urllib
from time import time
from Plugin import Plugin

class ZippyshareCom(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "ZippyshareCom"
        props['type'] = "hoster"
        props['pattern'] = r"(http://)?www?\d{0,2}\.zippyshare.com/v/"
        props['version'] = "0.1"
        props['description'] = """Zippyshare.com Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = props
        self.parent = parent
        self.html = None
        self.want_reconnect = False
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
        self.time_plus_wait = time() + 10
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_url = urllib.unquote(re.search("var comeonguys = 'fck(.*)';", self.html).group(1))
            return file_url
        else:
            return False
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search("<strong>Name: </strong>(.*)</font><br />", self.html).group(1)
            print file_name
        else:
            return self.parent.url
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r"HTTP Status 404", self.html) != None:
            return False
        else:
            return True
