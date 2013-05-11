#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json

from module.plugins.Crypter import Crypter

API_KEY = "AIzaSyCKnWLNlkX-L4oD1aEzqqhRw1zczeD6_k0"

class YoutubeBatch(Crypter):
    __name__ = "YoutubeBatch"
    __type__ = "container"
    __pattern__ = r"https?://(?:[^/]*?)youtube\.com/(?:(?:view_play_list|playlist|.*?feature=PlayList).*?[?&](?:list|p)=)([a-zA-Z0-9-_]+)"
    __version__ = "0.93"
    __description__ = """Youtube.com Channel Download Plugin"""
    __author_name__ = ("RaNaN", "Spoob", "zoidberg", "roland")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "zoidberg@mujmail.cz", "roland@enkore.de")

    def get_videos(self, playlist_id, token=None):
        url = "https://www.googleapis.com/youtube/v3/playlistItems?playlistId=%s&part=snippet&key=%s&maxResults=50" % (playlist_id, API_KEY)
        if token:
            url += "&pageToken=" + token

        response = json.loads(self.load(url))

        for item in response["items"]:
            if item["kind"] == "youtube#playlistItem" and item["snippet"]["resourceId"]["kind"] == "youtube#video":
                yield "http://youtube.com/watch?v=" + item["snippet"]["resourceId"]["videoId"]

        if "nextPageToken" in response:
            for item in self.get_videos(playlist_id, response["nextPageToken"]):
                yield item

    def decrypt(self, pyfile):
        match_id = re.match(self.__pattern__, self.pyfile.url)
        new_links = []
        playlist_id = match_id.group(1)

        new_links.extend(self.get_videos(playlist_id))

        self.packages.append((self.pyfile.package().name, new_links, self.pyfile.package().name))
