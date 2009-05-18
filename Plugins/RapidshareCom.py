#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import re
import time

from Plugin import Plugin
from time import time

class RapidshareCom(Plugin):
    
    def __init__(self, parent):
        self.plugin_name = "Rapidshare.com"
        self.plugin_pattern = r"http://(?:www.)?rapidshare.com/files/"
        self.plugin_type = "hoster"
        self.plugin_config = {}
        pluginProp = {}
        pluginProp ['name'] = "RapidshareCom"
        pluginProp ['version'] = "0.1"
        pluginProp ['format'] = "*.py"
        pluginProp ['description'] = """Rapidshare Plugin"""
        pluginProp ['author'] = "spoob"
        pluginProp ['author_email'] = "nn@nn.de"
        self.pluginProp = pluginProp 
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
        """ gets the url from self.parent.url saves html in self.html and parses
        """ 
        url = self.parent.url
        html = urllib2.urlopen(url).read()
        self.html = html
        self.html_old = time()
        file_server_url = re.search(r"<form action=\"(.*?)\"", self.html).group(1)
        free_user_encode = urllib.urlencode({"dl.start" : "Free"})
        self.html = urllib2.urlopen(file_server_url, free_user_encode).read()
        if re.search(r".*is already downloading.*", self.html) != None:
            self.time_plus_wait = time() + 10*60
        try:
            wait_minutes = re.search(r"Or try again in about (\d+) minute", self.html).group(1)
            self.time_plus_wait = time() + 60 * wait_minutes
        except:
            if re.search(r".*Currently a lot of users.*", self.html) != None:
                return ('wait', 2*60)  
            wait_seconds = re.search(r"var c=(.*);.*", self.html).group(1)
            self.time_plus_wait = time() + int(wait_seconds)

	print self.time_plus_wait - time()
    
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r".*The File could not be found.*", self.html) != None or \
           re.search(r"(<p>This limit is reached.</p>)", self.html) or \
           re.search(r"(.*is momentarily not available.*)", self.html):
            return False
        else:
            return True
	#The uploader has removed this file from the server.

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        if (self.html_old + 5*60) > time(): # nach einiger zeit ist die file_url nicht mehr aktuell
            self.download_html()

        file_url_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
        return re.search(file_url_pattern, self.html).group(1)
    
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        file_name_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
        return re.search(file_name_pattern, self.html).group(1).split('/')[-1]
    
    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
    
    def __call__(self):
        return self.plugin_name
