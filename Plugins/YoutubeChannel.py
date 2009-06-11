#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

    def file_exists(self):
        """ returns True or False
        """
        return True

    def proceed(self, url, location):
        self.user = re.search(r"/user/(.+)", self.parent.url).group(1)
        max_videos = self.config['max_videos']
        if not max_videos:
            new_links = None
            temp_links = []
            start_index = 1
            while(new_links != []):
                url = "http://gdata.youtube.com/feeds/api/users/" + self.user + "/uploads?max-results=50&start-index=" + str(start_index)
                rep = self.req.load(url)
                new_links = re.findall(r"href\='(http:\/\/www.youtube.com\/watch\?v\=[^']+)", rep)
                if new_links != []:
                    temp_links.extend(new_links)
                start_index += 50
            self.links = temp_links
        else:
            url = "http://gdata.youtube.com/feeds/api/users/" + self.user + "/uploads?max-results=" + max_videos
            rep = self.req.load(url)
            self.links = re.findall(r"href\='(http:\/\/www.youtube.com\/watch\?v\=[^']+)", rep)
