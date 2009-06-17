#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from Plugin import Plugin

class YoutubeCom(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "YoutubeCom"
        props['type'] = "hoster"
        props['pattern'] = r"http://(www\.)?(de\.)?\youtube\.com/watch\?v=.*"
        props['version'] = "0.2"
        props['description'] = """Youtube.com Video Download Plugin"""
        props['author_name'] = ("spoob")
        props['author_mail'] = ("spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.read_config()

    def download_html(self):
        url = self.parent.url
        self.html = self.req.load(url)

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        if self.html == None:
            self.download_html()

        videoId = self.parent.url.split("v=")[1].split("&")[0]
        videoHash = re.search(r', "t": "([^"]+)"', self.html).group(1)
        quality = ""
        if self.config['high_quality']:
            quality = "&fmt=18"
        file_url = 'http://youtube.com/get_video?video_id=' + videoId + '&t=' + videoHash + quality
        return file_url

    def get_file_name(self):
        if self.html == None:
            self.download_html()

        file_name_pattern = r"<title>YouTube - (.*)</title>"
        file_suffix = ".flv"
        if self.config['high_quality']:
            file_suffix = ".mp4"
        return re.search(file_name_pattern, self.html).group(1).replace("/", "") + file_suffix

    def file_exists(self):
        """ returns True or False
        """
        if self.html == None:
            self.download_html()
        if re.search(r"(.*eine fehlerhafte Video-ID\.)", self.html) != None:
            return False
        else:
            return True
