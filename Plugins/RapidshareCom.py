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
        Plugin.__init__(self, parent)
        plugin_config = {}
        plugin_config['name'] = "RapidshareCom"
        plugin_config['type'] = "hoster"
        plugin_config['pattern'] = r"http://(?:www.)?rapidshare.com/files/"
        plugin_config['version'] = "0.1"
        plugin_config['description'] = """Rapidshare.com Download Plugin"""
        plugin_config['author_name'] = ("spoob")
        plugin_config['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = plugin_config
        self.parent = parent
        self.html = [None, None]
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.want_reconnect = False
        self.multi_dl = False
    
    def set_parent_status(self):
        """ sets all available Statusinfos about a File in self.parent.status
        """
        if self.html[0] == None:
            self.download_html()

        self.get_wait_time()
        self.parent.status.filename = self.get_file_name()
        self.parent.status.url = self.get_file_url()
        self.parent.status.waituntil = self.wait_until()
    
    def download_html(self):
        """ gets the url from self.parent.url saves html in self.html and parses
        """ 
        url = self.parent.url
        html = self.req.load(url)
        self.html[0] = html
        self.html_old = time()

    def download_serverhtml(self):
        """downloads html with the important informations
        """
        if self.html[0] == None:
            self.download_html()
        
        file_server_url = re.search(r"<form action=\"(.*?)\"", self.html[0]).group(1)
        #free user
        #free_user_encode = urllib.urlencode({"dl.start" : "Free"})
        self.html[1] = self.req.load(file_server_url, None,{"dl.start" : "Free"})
        self.html_old = time()
        self.get_wait_time()
        
        
    def get_wait_time(self):

        if self.html[1] == None:
            download_serverhtml(self)
        
        if re.search(r".*is already downloading.*", self.html[1]) != None:
            self.time_plus_wait = time() + 10*60
        try:
            wait_minutes = re.search(r"Or try again in about (\d+) minute", self.html[1]).group(1)
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            if re.search(r".*Currently a lot of users.*", self.html[1]) != None:
                self.time_plus_wait = time() + 2*60
            wait_seconds = re.search(r"var c=(.*);.*", self.html[1]).group(1)
            self.time_plus_wait = time() + int(wait_seconds) + 5
    
    def file_exists(self):
        """ returns True or False 
        """
        if self.html[0] == None:
            self.download_html()
        if re.search(r".*The File could not be found.*", self.html[0]) != None or \
           re.search(r"(<p>This limit is reached.</p>)", self.html[0]) or \
           re.search(r"(.*is momentarily not available.*)", self.html[0]) or \
           re.search(r"(.*The uploader has removed this file from the server.*)", self.html[0]) or \
	   re.search(r"(.*This file is suspected to contain illegal content.*)", self.html[0]):
	    return False
        else:
            return True

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[1] == None:
            self.download_serverhtml()
        if (self.html_old + 5*60) < time(): # nach einiger zeit ist die file_url nicht mehr aktuell
            self.download_serverhtml()

        if not self.want_reconnect:
            file_url_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
            return re.search(file_url_pattern, self.html[1]).group(1)
        else:
            return False
    
    def get_file_name(self):
        if self.html[1] == None:
            self.download_serverhtml()
        if not self.want_reconnect:
            file_name_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
            return re.search(file_name_pattern, self.html[1]).group(1).split('/')[-1]
        else:
            return self.parent.url
    
    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
    
    def __call__(self):
        return self.plugin_config['name']
