#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from time import time
from module.network.Request import Request

class Plugin():
    
    def __init__(self, parent):
        self.plugin_name = None
        self.plugin_pattern = None
        self.plugin_type = "hoster"
        pluginProp = {}
        pluginProp ['name'] = "Base Plugin"
        pluginProp ['version'] = "0.1"
        pluginProp ['format'] = "*.py"
        pluginProp ['description'] = """bla"""
        pluginProp ['author'] = "Spoob"
        pluginProp ['author_email'] = "nn@nn.de"
        self.pluginProp = pluginProp 
        self.parent = parent
        self.req = Request()
        self.html = None
        self.time_plus_wait = None #time() + wait in seconds
        self.want_reconnect = None
        self.multi_dl = True
    
    def set_parent_status(self):
        """ sets all available Statusinfos about a File in self.parent.status
        """
        pass
    
    def download_html(self):
        """ gets the url from self.parent.url saves html in self.html and parses
        """ 
        html = ""
        self.html = html
    
    def file_exists(self):
        """ returns True or False 
        """
        return True
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        return self.parent.url

    
    def get_file_name(self):
        return re.findall("([^\/=]+)",self.parent.url)[-1]
    
    def wait_until(self):
        if self.html != None:
            self.download_html()
        return self.time_plus_wait
    
    def proceed(self, url, location):
        self.req.download(url, location)
    
    def __call__(self):
        return self.plugin_name
