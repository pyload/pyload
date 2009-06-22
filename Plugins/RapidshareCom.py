#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from time import time

from Plugin import Plugin

class RapidshareCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RapidshareCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(?:www.)?(rs\d*.)?rapidshare.com/files/"
        props['version'] = "0.1"
        props['description'] = """Rapidshare.com Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = [None, None]
        self.html_old = None         #time() where loaded the HTML
        self.time_plus_wait = None   #time() + wait in seconds
        self.want_reconnect = False
        self.multi_dl = False

        self.read_config()
        if self.config['premium']:
            self.multi_dl = True

    def prepare(self, thread):
        pyfile = self.parent

        self.want_reconnect = False

        self.download_html()

        pyfile.status.exists = self.file_exists()

        if not pyfile.status.exists:
            raise Exception, "The file was not found on the server."

        self.download_serverhtml()

        pyfile.status.filename = self.get_file_name()

        pyfile.status.waituntil = self.time_plus_wait
        pyfile.status.url = self.get_file_url()
        pyfile.status.want_reconnect = self.want_reconnect


        thread.wait(self.parent)

        return True

    def download_html(self):
        """ gets the url from self.parent.url saves html in self.html and parses
        """
        url = self.parent.url
        html = self.req.load(url)
        self.html[0] = html
        self.html_old = time()

        self.download_serverhtml()

    def download_serverhtml(self):
        """downloads html with the important informations
        """
        if self.html[0] == None:
            self.download_html()

        if self.config['premium']:
            return False

        file_server_url = re.search(r"<form action=\"(.*?)\"", self.html[0]).group(1)
        self.html[1] = self.req.load(file_server_url, None, {"dl.start": "Free"})
        self.html_old = time()
        self.get_wait_time()

    def get_wait_time(self):

        if self.config['premium']:
            self.time_plus_wait = 0
            return True

        if self.html[1] == None:
            self.download_serverhtml(self)

        if re.search(r".*is already downloading.*", self.html[1]) != None:
            self.time_plus_wait = time() + 10 * 60
        try:
            wait_minutes = re.search(r"Or try again in about (\d+) minute", self.html[1]).group(1)
            self.time_plus_wait = time() + 60 * int(wait_minutes)
            self.want_reconnect = True
        except:
            if re.search(r".*Currently a lot of users.*", self.html[1]) != None:
                self.time_plus_wait = time() + 2 * 60
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
        if self.config['premium']:
            return self.parent.url

        if self.html[1] == None:
            self.download_serverhtml()

        if (self.html_old + 5 * 60) < time(): # nach einiger zeit ist die file_url nicht mehr aktuell
            self.download_serverhtml()

        if not self.want_reconnect:
            file_url_pattern = r".*name=\"dlf\" action=\"(.*)\" method=.*"
            return re.search(file_url_pattern, self.html[1]).group(1)
        else:
            raise Exception, "Error when retrieving download url"

    def get_file_name(self):
        if self.html[0] == None:
            self.download_html()
            
        file_name_pattern = r"<p class=\"downloadlink\">.+/(.+)<font"
        return re.findall(file_name_pattern, self.html[0])[0]

    def proceed(self, url, location):

        if self.config['premium']:
            self.req.add_auth(self.config['username'], self.config['password'])

        self.req.download(url, location)
