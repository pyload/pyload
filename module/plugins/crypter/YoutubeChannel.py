#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class YoutubeChannel(Crypter):
    __name__ = "YoutubeChannel"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?(de\.)?\youtube\.com/user/*"
    __version__ = "0.9"
    __description__ = """Youtube.com Channel Download Plugin"""
    __author_name__ = ("RaNaN", "Spoob")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org")

    def __init__(self, parent):
        Crypter.__init__(self, parent)
        self.parent = parent
        self.html = None
        self.read_config()
        self.user = re.search(r"/user/(.+)", self.parent.url).group(1).split("#")[0]

    def file_exists(self):
        if "User not found" in self.req.load("http://gdata.youtube.com/feeds/api/users/%s" % self.user):
            return False
        return True

    def proceed(self, url, location):
        max_videos = self.config['max_videos']
        if not max_videos:
            max_videos = 1000 #max video a user can upload
        page = 0
        temp_links = []
        if "," in self.config['video_groups']:
            video_groups = self.config['video_groups'].split(",")
        else:
            video_groups = [self.config['video_groups']]
        for group in video_groups:
            for start_index in range(1, int(max_videos), 50):
                max_results = max_videos - page * 50
                if max_results > 50:
                    max_results = 50
                url = "http://gdata.youtube.com/feeds/api/users/%s/%s?max-results=%i&start-index=%i" % (self.user, group, max_results, start_index)
                rep = self.req.load(url)
                new_links = re.findall(r"href\='(http:\/\/www.youtube.com\/watch\?v\=[^']+)&", rep)
                if new_links != []:
                    temp_links.extend(new_links)
                else:
                    break
                page += 1
        self.links = temp_links
