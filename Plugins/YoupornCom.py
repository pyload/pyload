#!/usr/bin/env python

import re
from Plugin import Plugin

class YoupornCom(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "YoupornCom"
        props['type'] = "hoster"
	props['pattern'] = r"http://(www\.)?youporn\.com/watch/.+"
        props['version'] = "0.1"
        props['description'] = """Youporn.com Video Download Plugin"""
        props['author_name'] = ("willnix")
        props['author_mail'] = ("willnix@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
    
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

        file_url = re.search(r'(http://download.youporn.com/download/\d*/.*\?download=1&ll=1&t=dd)">', self.html).group(1)
	print file_url
	return file_url
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
       	file_name_pattern = r".*<title>(.*) - Free Porn Videos - YouPorn.com Lite \(BETA\)</title>.*"
	return re.search(file_name_pattern, self.html).group(1) + '.flv'
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(.*invalid video_id.*)", self.html) != None:
            return False
        else:
            return True
