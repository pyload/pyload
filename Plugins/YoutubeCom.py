#!/usr/bin/env python

import urllib2
import re
from time import time
from Plugin import Plugin

class YoutubeCom(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        self.plugin_name = "Youtube.com"
        self.plugin_pattern = r"http://(www\.)?(de\.)?\youtube\.com/watch\?v=(.*)"
        self.plugin_type = "hoster"
        self.plugin_config = {}
        pluginProp = {}
        pluginProp ['name'] = "YoutubeCom"
        pluginProp ['version'] = "0.1"
        pluginProp ['format'] = "*.py"
        pluginProp ['description'] = """Youtube Plugin"""
        pluginProp ['author'] = "spoob"
        pluginProp ['author_email'] = "spoob@pyload.org"
        self.pluginProp = pluginProp 
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.want_reconnect = None
    
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
            videoId = re.search(self.plugin_pattern, self.parent.url).group(3)
            videoHash = re.search(r', "t": "([^"]+)"', self.html).group(1)
            file_url = 'http://youtube.com/get_video?video_id=' + videoId + '&t=' + videoHash + '&fmt=18'
            return file_url
        else:
            return False
        
    def get_file_name(self):
        if self.html == None:
            self.download_html()
        if not self.want_reconnect:
            file_name_pattern = r"<title>YouTube - (.*)</title>"
            return re.search(file_name_pattern, self.html).group(1).replace("/", "") + '.mp4'
        else:
            return self.parent.url
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(.*eine fehlerhafte Video-ID\.)", self.html) != None:
            return False
        else:
            return True

    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
    
    def __call__(self):
        return self.plugin_name
