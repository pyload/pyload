#!/usr/bin/python
# -*- coding: utf-8 -*-

from time import time
from module.network.Request import Request

class Plugin():
    
    def __init__(self, parent):
        self.plugin_name = None
        self.plugin_pattern = None
        self.plugin_type = ""
        pluginProp = {}
        pluginProp ['name'] = "Beispiel Plugin"
        pluginProp ['version'] = "0.1"
        pluginProp ['format'] = "*.py"
        pluginProp ['description'] = """bla"""
        pluginProp ['author'] = "Author"
        pluginProp ['author_email'] = "nn@nn.de"
        self.pluginProp = pluginProp 
        self.parent = parent
        self.req = Request()
        self.html = None
        self.time_plus_wait = None #time() + wait in seconds
        self.want_reconnect = None
    
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
        if self.html != None:
            self.download_html()
        
    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html != None:
            self.download_html()
    
    def get_file_name(self):
        raise NotImplementedError
    
    def wait_until(self):
        if self.html != None:
            self.download_html()
        return self.time_plus_wait
        
    
    def __call__(self):
        return self.plugin_name
