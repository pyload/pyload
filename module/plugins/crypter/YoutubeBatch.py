#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class YoutubeBatch(Crypter):
    __name__ = "YoutubeBatch"
    __type__ = "container"
    __pattern__ = r"http://(www\.)?(de\.)?\youtube\.com/user/*"
    __version__ = "0.9"
    __description__ = """Youtube.com Channel Download Plugin"""
    __author_name__ = ("RaNaN", "Spoob")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org")

    def setup(self):
        self.user = re.search(r"/user/(.+)", self.pyfile.url).group(1).split("#")[0]
        self.playlist = re.search(r"/user/%s.*?/user/(.{16})" % self.user, self.pyfile.url).group(1)

    def file_exists(self):
        if "User not found" in self.req.load("http://gdata.youtube.com/feeds/api/playlists/%s?v=2" % self.playlist):
            return False
        return True

    def decrypt(self, pyfile):
        if not self.file_exists():
            self.offline()
        url = "http://gdata.youtube.com/feeds/api/playlists/%s?v=2" % self.playlist           
        rep = self.load(url)
        new_links = []
        new_links.extend(re.findall(r"href\='(http:\/\/www.youtube.com\/watch\?v\=[^']+)&", rep))
        self.packages.append((self.pyfile.package().name, new_links, self.pyfile.package().name))
