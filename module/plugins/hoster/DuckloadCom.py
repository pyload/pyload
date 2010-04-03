#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.Plugin import Plugin
from time import time

class DuckloadCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "DuckloadCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www\.)?duckload\.com/divx/"
        props['version'] = "0.1"
        props['description'] = """Duckload.com Download Plugin"""
        props['author_name'] = ("wugy")
        props['author_mail'] = ("wugy@qip.ru")
        self.props = props
        self.parent = parent
        self.html = [None, None]
        self.want_reconnect = False
        self.multi_dl = False
    
    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False
        
        self.download_html()
        
        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            raise Exception, "The file was not found on the server."
            return False

        pyfile.status.filename = self.get_file_name()
            
        pyfile.status.waituntil = time()
        pyfile.status.url = self.get_file_url()
        pyfile.status.want_reconnect = self.want_reconnect

        thread.wait(self.parent)

        return True

    def download_html(self):
        url = self.parent.url
        self.html[0] = self.req.load(url, cookies=True)
        self.html[1] = self.req.load(url, cookies=True, post={"server": "1", "sn": "Stream Starten"})

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html[1] == None:
            self.download_html()
        if not self.want_reconnect:
            file_url = re.search('type=\"video/divx\"\ src=\"(.*?)\"', self.html[1]).group(1)
            #print file_url
            return file_url
        else:
            return False

    def get_file_name(self):
        if self.html[1] == None:
            self.download_html()
        if not self.want_reconnect:
            file_name = re.search('Film\ \"(\S*?)\"\ anschauen', self.html[1]).group(1)
            return file_name
        else:
            return self.parent.url

    def file_exists(self):
        """ returns True or False
        """
        if self.html[0] == None:
            self.download_html()
        if re.search(r"Datei wurde nicht gefunden!", self.html) != None:
            return False
        else:
            return True

    def proceed(self, url, location):
        self.req.download(url, location, cookies=True)

