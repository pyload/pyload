#!/usr/bin/env python

import re
from Plugin import Plugin

class MyvideoDe(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "MyvideoDe"
        props['type'] = "hoster"
        props['pattern'] = r"http://(www\.)?myvideo.de/watch/"
        props['version'] = "0.1"
        props['description'] = """Youtube.com Video Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
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
        url = self.parent.url
        self.html = self.req.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()
        videoId = re.search(r"addVariable\('_videoid','(.*)'\);p.addParam\('quality'", self.html).group(1)
        videoServer = re.search("rel='image_src' href='(.*)thumbs/.*' />", self.html).group(1)
        file_url = videoServer + videoId + ".flv"
        print videoId
        print videoServer
        print file_url
        return file_url

    def get_file_name(self):
        if self.html == None:
            self.download_html()
        file_name_pattern = r"<h1 class='globalHd'>(.*)</h1>"
        return re.search(file_name_pattern, self.html).group(1).replace("/", "") + '.flv'

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(.* Das angeforderte Video ist nicht.*)", self.html) != None:
            return False
        else:
            return True
