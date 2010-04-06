#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.Plugin import Plugin

class YoutubeChannel(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "YoutubeChannel"
        props['type'] = "container"
        props['pattern'] = r"http://(www\.)?(de\.)?\youtube\.com/user/*"
        props['version'] = "0.9"
        props['description'] = """Youtube.com Channel Download Plugin"""
        props['author_name'] = ("RaNaN", "Spoob")
        props['author_mail'] = ("RaNaN@pyload.org", "spoob@pyload.org")
        self.props = props
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
