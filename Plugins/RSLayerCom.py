#!/usr/bin/env python

import re
from Plugin import Plugin
import module.unescape

class XupIn(Plugin):
    
    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RSLayerCom"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?rs-layer.com/"
        props['version'] = "0.1"
        props['description'] = """RSLayer.com Decrypt Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.plugin_config = props
        self.parent = parent
        self.html = None
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.posts = {}
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
        
    def file_exists(self):
        """ returns True or False 
        """
        if self.html == None:
            self.download_html()
        if re.search(r"File nicht da", self.html, re.I) != None:
            return False
        else:
            return True

    def proceed():
        while re.search(r".*onclick=\"getFile\(\'([0-9]{6}-.{8})\'\);changeBackgroundColor.*", content, re.I) != None:
            found = re.search(r".*onclick=\"getFile\(\'([0-9]{6}-.{8})\'\);changeBackgroundColor.*", content, re.I).group(1)
            content = content.replace('getFile(\'' + found + '\');changeBackgroundColor', '')
            decryptedUrl = unescape(re.search(r".*<iframe src=\"(.*)\" marginhei.*", urllib2.urlopen("http://rs-layer.com/link-"+ found + ".html").read(), re.I).group(1))
            
            self.links.append(decryptedUrl)

    def wait_until(self):
        if self.html == None:
            self.download_html()
        return self.time_plus_wait
