#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class YoutubeBatch(Crypter):
    __name__ = "YoutubeBatch"
    __type__ = "container"
    __pattern__ = r"http://(?:[^/]*?)youtube\.com/((?:view_play_list|playlist|.*?feature=PlayList).*?[\?&](?:list|p)=|user/)(\w+)"
    __version__ = "0.92"
    __description__ = """Youtube.com Channel Download Plugin"""
    __author_name__ = ("RaNaN", "Spoob", "zoidberg")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "zoidberg@mujmail.cz")

    def decrypt(self, pyfile):
        match_id = re.match(self.__pattern__, self.pyfile.url)
        if match_id.group(1) == "user/":
            url = "http://gdata.youtube.com/feeds/api/users/%s/uploads?v=2" % match_id.group(2)
        else:
            url = "http://gdata.youtube.com/feeds/api/playlists/%s?v=2" % match_id.group(2)

        rep = self.load(url)
        new_links = []
        new_links.extend(re.findall(r"href\='(http:\/\/www.youtube.com\/watch\?v\=[^']+)&", rep))
        self.packages.append((self.pyfile.package().name, new_links, self.pyfile.package().name))
