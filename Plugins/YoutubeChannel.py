#!/usr/bin/env python

import re

from Plugin import Plugin

class YoutubeChannel(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "YoutubeChannel"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?(de\.)?\youtube\.com/user/*"
        props['version'] = "0.2"
        props['description'] = """Youtube.com Channel Download Plugin"""
        props['author_name'] = ("RaNaN", "Spoob")
        props['author_mail'] = ("RaNaN@pyload.org", "Spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.html = None
        self.read_config()

    def download_html(self):
        self.html = "Not needed"

    def get_file_url(self):
        """ returns the absolute downloadable filepath
        """
        self.user = re.search(r"/user/(.+)", self.parent.url).group(1)
        max_videos = ""
        if self.config['max_videos']:
            max_videos = "?max-results=" + self.config['max_videos']
        url = "http://gdata.youtube.com/feeds/api/users/" + self.user + "/uploads" + max_videos
        return url

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        rep = self.req.load(url)
        self.links = re.findall(r"href\='(http:\/\/www.youtube.com\/watch\?v\=[^']+)", rep)
