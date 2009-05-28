#!/usr/bin/env python

import re
from time import time
from Plugin import Plugin

class UploadedTo(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "UploadedTo"
        props['type'] = "hoster"
        props['pattern'] = r"http://(www\.)?uploaded.to/"
        props['version'] = "0.1"
        props['description'] = """Uploaded.to Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = props
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
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

        try:
            wait_minutes = re.search(r"Or wait (\d+) minutes", self.html).group(1)
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            self.time_plus_wait = 0
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if not self.want_reconnect: 
            file_url_pattern = r".*<form name=\"download_form\" method=\"post\" action=\"(.*)\">"
            return re.search(file_url_pattern, self.html).group(1)
        else:
            return False
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search(r"<td><b>\s+(.+)\s", self.html).group(1) + re.search(r"</td><td>(\..+)</td></tr>", self.html).group(1)

            #file_name_pattern = r"<title>\s*(.*?)\s+\.\.\."
            return file_name
        else:
            return self.parent.url
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(File doesn't exist .*)", self.html) != None:
            return False
        else:
            return True

    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
