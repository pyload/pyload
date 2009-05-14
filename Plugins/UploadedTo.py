#!/usr/bin/env python

import urllib2
import re
from Plugin import Plugin

class UploadedTo(Plugin):
    
    def __init__(self, parent):
        self.plugin_name = "Uploaded.to"
        self.plugin_pattern = r"http://(www\.)?uploaded.to/"
        self.plugin_type = "hoster"
        self.plugin_config = {}
        pluginProp = {}
        pluginProp ['name'] = "UploadedTo"
        pluginProp ['version'] = "0.1"
        pluginProp ['format'] = "*.py"
        pluginProp ['description'] = """Uploaded Plugin"""
        pluginProp ['author'] = "spoob"
        pluginProp ['author_email'] = "spoob@gmx.de"
        self.pluginProp = pluginProp 
        self.parent = parent
        self.html = ""
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
        html = urllib2.urlopen(url).read()
        try:
            wait_minutes = re.search(r"Or wait (\d+) minutes", self.html).group(1)
            self.time_plus_wait = time() + 60 * wait_minutes
        except:
            self.time_plus_wait = 0
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        file_url_pattern = r".*<form name=\"download_form\" method=\"post\" action=\"(.*)\">"
        return re.search(file_url_pattern, self.html).group(1)
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        file_name_pattern = r"<title>\s*(.*?)\s+\.\.\."
        return re.search(file_name_pattern, self.html).group(1)
        
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
    
    def __call__(self):
        return self.plugin_name
