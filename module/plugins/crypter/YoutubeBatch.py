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

from urlparse import urljoin
import re

from module.common.json_layer import json_loads
from module.plugins.Crypter import Crypter
from module.utils import save_join

API_KEY = "AIzaSyCKnWLNlkX-L4oD1aEzqqhRw1zczeD6_k0"


class YoutubeBatch(Crypter):
    __name__ = "YoutubeBatch"
    __type__ = "crypter"
    __pattern__ = r"https?://(?:www\.)?(m\.)?youtube\.com/(?P<TYPE>user|playlist|view_play_list)(/|.*?[?&](?:list|p)=)(?P<ID>[\w-]+)"
    __version__ = "1.00"
    __description__ = """Youtube.com channel & playlist decrypter"""
    __config__ = [("likes", "bool", "Grab user (channel) liked videos", "False"),
                  ("favorites", "bool", "Grab user (channel) favorite videos", "False"),
                  ("uploads", "bool", "Grab channel unplaylisted videos", "True")]
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def api_response(self, ref, req):
        req.update({"key": API_KEY})
        url = urljoin("https://www.googleapis.com/youtube/v3/", ref)
        page = self.load(url, get=req)
        return json_loads(page)

    def getChannel(self, user):
        channels = self.api_response("channels", {"part": "id,snippet,contentDetails", "forUsername": user, "maxResults": "50"})
        if channels["items"]:
            channel = channels["items"][0]
            return {"id": channel["id"],
                    "title": channel["snippet"]["title"],
                    "relatedPlaylists": channel["contentDetails"]["relatedPlaylists"],
                    "user": user}  # One lone channel for user?

    def getPlaylist(self, p_id):
        playlists = self.api_response("playlists", {"part": "snippet", "id": p_id})
        if playlists["items"]:
            playlist = playlists["items"][0]
            return {"id": p_id,
                    "title": playlist["snippet"]["title"],
                    "channelId": playlist["snippet"]["channelId"],
                    "channelTitle": playlist["snippet"]["channelTitle"]}

    def _getPlaylists(self, id, token=None):
        req = {"part": "id", "maxResults": "50", "channelId": id}
        if token:
            req.update({"pageToken": token})

        playlists = self.api_response("playlists", req)

        for playlist in playlists["items"]:
            yield playlist["id"]

        if "nextPageToken" in playlists:
            for item in self._getPlaylists(id, playlists["nextPageToken"]):
                yield item

    def getPlaylists(self, ch_id):
        return map(self.getPlaylist, self._getPlaylists(ch_id))

    def _getVideosId(self, id, token=None):
        req = {"part": "contentDetails", "maxResults": "50", "playlistId": id}
        if token:
            req.update({"pageToken": token})

        playlist = self.api_response("playlistItems", req)

        for item in playlist["items"]:
            yield item["contentDetails"]["videoId"]

        if "nextPageToken" in playlist:
            for item in self._getVideosId(id, playlist["nextPageToken"]):
                yield item

    def getVideosId(self, p_id):
        return list(self._getVideosId(p_id))

    def decrypt(self, pyfile):
        match = re.match(self.__pattern__, pyfile.url)
        m_id = match.group("ID")
        m_type = match.group("TYPE")

        if m_type == "user":
            self.logDebug("Url recognized as Channel")
            user = m_id
            channel = self.getChannel(user)

            if channel:
                playlists = self.getPlaylists(channel["id"])
                self.logDebug("%s playlist\s found on channel \"%s\"" % (len(playlists), channel["title"]))

                relatedplaylist = {p_name: self.getPlaylist(p_id) for p_name, p_id in channel["relatedPlaylists"].iteritems()}
                self.logDebug("Channel's related playlists found = %s" % relatedplaylist.keys())

                relatedplaylist["uploads"]["title"] = "Unplaylisted videos"
                relatedplaylist["uploads"]["checkDups"] = True  #: checkDups flag

                for p_name, p_data in relatedplaylist.iteritems():
                    if self.getConfig(p_name):
                        p_data["title"] += " of " + user
                        playlists.append(p_data)
            else:
                playlists = []
        else:
            self.logDebug("Url recognized as Playlist")
            playlists = [self.getPlaylist(m_id)]

        if not playlists:
            self.fail("No playlist available")

        addedvideos = []
        urlize = lambda x: "https://www.youtube.com/watch?v=" + x
        for p in playlists:
            p_name = p["title"]
            p_videos = self.getVideosId(p["id"])
            p_folder = save_join(self.config['general']['download_folder'], p["channelTitle"], p_name)
            self.logDebug("%s video\s found on playlist \"%s\"" % (len(p_videos), p_name))

            if not p_videos:
                continue
            elif "checkDups" in p:
                p_urls = [urlize(v_id) for v_id in p_videos if v_id not in addedvideos]
                self.logDebug("%s video\s available on playlist \"%s\" after duplicates cleanup" % (len(p_urls), p_name))
            else:
                p_urls = map(urlize, p_videos)

            self.packages.append((p_name, p_urls, p_folder))  #: folder is NOT recognized by pyload 0.4.9!

            addedvideos.extend(p_videos)
