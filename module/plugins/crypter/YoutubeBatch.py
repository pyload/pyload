#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: Walter Purcaro
"""

import re
import json

from module.plugins.Crypter import Crypter
from os.path import join

API_KEY = "AIzaSyCKnWLNlkX-L4oD1aEzqqhRw1zczeD6_k0"


class YoutubeBatch(Crypter):
    __name__ = "YoutubeBatch"
    __type__ = "container"
    __pattern__ = r"https?://(?:[^/]*?)youtube\.com/(?:(view_play_list|playlist|.*?feature=PlayList|user)(?:.*?[?&](?:list|p)=|/))([a-zA-Z0-9-_]+)"
    __version__ = "0.94"
    __description__ = """Youtube.com Channel Download Plugin"""
    __author_name__ = ("RaNaN", "Spoob", "zoidberg", "roland", "Walter Purcaro")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "zoidberg@mujmail.cz", "roland@enkore.de", "vuolter@gmail.com")

    def json_response(self, api, req):
        req.update({"key": API_KEY})
        url = "https://www.googleapis.com/youtube/v3/" + api
        page = self.load(url, get=req)
        return json.loads(page)

    def get_playlist_baseinfos(self, playlist_id):
        res = self.json_response("playlists", {"part": "snippet", "id": playlist_id})

        snippet = res["items"][0]["snippet"]
        playlist_name = snippet["title"]
        channel_title = snippet["channelTitle"]
        return playlist_name, channel_title

    def get_channel_id(self, user_name):
        res = self.json_response("channels", {"part": "id", "forUsername": user_name})
        return res["items"][0]["id"]

    def get_playlists(self, user_name, token=None):
        channel_id = self.get_channel_id(user_name)
        req = {"part": "id", "maxResults": "50", "channelId": channel_id}
        if token:
            req.update({"pageToken": token})
        res = self.json_response("playlists", req)

        for item in res["items"]:
            yield item["id"]

        if "nextPageToken" in res:
            for item in self.get_playlists(user_name, res["nextPageToken"]):
                yield item

    def get_videos(self, playlist_id, token=None):
        req = {"part": "snippet", "maxResults": "50", "playlistId": playlist_id}
        if token:
            req.update({"pageToken": token})
        res = self.json_response("playlistItems", req)

        for item in res["items"]:
            yield "http://youtube.com/watch?v=" + item["snippet"]["resourceId"]["videoId"]

        if "nextPageToken" in res:
            for item in self.get_videos(playlist_id, res["nextPageToken"]):
                yield item

    def decrypt(self, pyfile):
        match_obj = re.match(self.__pattern__, pyfile.url)
        match_type, match_result = match_obj.group(1), match_obj.group(2)
        playlist_ids = []

        #: is a channel username or just a playlist id?
        if match_type == "user":
            ids = self.get_playlists(match_result)
            playlist_ids.extend(ids)
        else:
            playlist_ids.append(match_result)

        self.logDebug("Playlist IDs = %s" % playlist_ids)

        if not playlist_ids:
            self.fail("Wrong url")

        for id in playlist_ids:
            self.logDebug("Processing playlist id: %s" % id)

            playlist_name, channel_title = self.get_playlist_baseinfos(id)
            video_links = [x for x in self.get_videos(id)]

            self.logInfo("%s videos found on playlist \"%s\" (channel \"%s\")" % (len(video_links), playlist_name, channel_title))
            self.logDebug("Video links = %s" % video_links)

            if not video_links:
                continue

            folder = join(self.config['general']['download_folder'], channel_title, playlist_name)
            self.packages.append((playlist_name, video_links, folder)) #Note: folder is NOT used actually!
