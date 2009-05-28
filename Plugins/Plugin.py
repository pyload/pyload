#!/usr/bin/python
# -*- coding: utf-8 -*-

import ConfigParser
import re

from module.network.Request import Request

class Plugin():
    
    def __init__(self, parent):
        self.plugin_name = "Base"
        self.plugin_pattern = None
        self.plugin_type = "hoster"
        self.parser = ConfigParser.SafeConfigParser()
        self.config = {}
        props = {}
        props['name'] = "Base Plugin"
        props['version'] = "0.1"
        props['format'] = "*.py"
        props['description'] = """bla"""
        props['author'] = "Spoob"
        props['author_email'] = "nn@nn.de"
        self.props = props
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
        return re.findall("([^\/=]+)", self.parent.url)[-1]
    
    def wait_until(self):
        if self.html != None:
            self.download_html()
        return self.time_plus_wait
    
    def proceed(self, url, location):
        self.req.download(url, location)

    def set_config(self):
        pass

    def get_config(self, value):
        self.parser.read("pluginconfig")
        return self.parser.get(self.props['name'], value)

    def read_config(self):
        self.parser.read("pluginconfig")

        if self.parser.has_section(self.props['name']):
            for option in self.parser.options(self.props['name']):
                self.config[option] = self.parser.get(self.props['name'], option)

    def __call__(self):
        return self.props['name']
