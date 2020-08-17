# -*- coding: utf-8 -*-

import json
import os
import re
import urllib.parse

from ..base.decrypter import BaseDecrypter


class YoutubeComFolder(BaseDecrypter):
    __name__ = "YoutubeComFolder"
    __type__ = "decrypter"
    __version__ = "1.09"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.|m\.)?youtube\.com/(?P<TYPE>user|playlist|view_play_list)(/|.*?[?&](?:list|p)=)(?P<ID>[\w\-]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
        ("likes", "bool", "Grab user (channel) liked videos", False),
        ("favorites", "bool", "Grab user (channel) favorite videos", False),
        ("uploads", "bool", "Grab channel unplaylisted videos", True),
    ]

    __description__ = """Youtube.com channel & playlist decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    API_KEY = "AIzaSyCKnWLNlkX-L4oD1aEzqqhRw1zczeD6_k0"

    def api_response(self, ref, req):
        req.update({"key": self.API_KEY})
        url = urllib.parse.urljoin("https://www.googleapis.com/youtube/v3/", ref)
        html = self.load(url, get=req)
        return json.loads(html)

    def get_channel(self, user):
        channels = self.api_response(
            "channels",
            {
                "part": "id,snippet,contentDetails",
                "forUsername": user,
                "maxResults": "50",
            },
        )
        if channels["items"]:
            channel = channels["items"][0]
            return {
                "id": channel["id"],
                "title": channel["snippet"]["title"],
                "relatedPlaylists": channel["contentDetails"]["relatedPlaylists"],
                "user": user,
            }  #: One lone channel for user?

    def get_playlist(self, p_id):
        playlists = self.api_response("playlists", {"part": "snippet", "id": p_id})
        if playlists["items"]:
            playlist = playlists["items"][0]
            return {
                "id": p_id,
                "title": playlist["snippet"]["title"],
                "channelId": playlist["snippet"]["channelId"],
                "channelTitle": playlist["snippet"]["channelTitle"],
            }

    def _get_playlists(self, id, token=None):
        req = {"part": "id", "maxResults": "50", "channelId": id}
        if token:
            req.update({"pageToken": token})

        playlists = self.api_response("playlists", req)

        for playlist in playlists["items"]:
            yield playlist["id"]

        if "nextPageToken" in playlists:
            for item in self._get_playlists(id, playlists["nextPageToken"]):
                yield item

    def get_playlists(self, ch_id):
        return [self.get_playlist(p_id) for p_id in self._get_playlists(ch_id)]

    def _get_videos_id(self, id, token=None):
        req = {"part": "contentDetails", "maxResults": "50", "playlistId": id}
        if token:
            req.update({"pageToken": token})

        playlist = self.api_response("playlistItems", req)

        for item in playlist["items"]:
            yield item["contentDetails"]["videoId"]

        if "nextPageToken" in playlist:
            for item in self._get_videos_id(id, playlist["nextPageToken"]):
                yield item

    def get_videos_id(self, p_id):
        return list(self._get_videos_id(p_id))

    def decrypt(self, pyfile):
        m = re.match(self.__pattern__, pyfile.url)
        m_id = m.group("ID")
        m_type = m.group("TYPE")

        if m_type == "user":
            self.log_debug("Url recognized as Channel")
            user = m_id
            channel = self.get_channel(user)

            if channel:
                playlists = self.get_playlists(channel["id"])
                self.log_debug(
                    r'{} playlist\s found on channel "{}"'.format(
                        len(playlists), channel["title"]
                    )
                )

                relatedplaylist = {
                    p_name: self.get_playlist(p_id)
                    for p_name, p_id in channel["relatedPlaylists"].items()
                }

                self.log_debug(
                    "Channel's related playlists found = {}".format(
                        list(relatedplaylist.keys())
                    )
                )

                relatedplaylist["uploads"]["title"] = "Unplaylisted videos"
                relatedplaylist["uploads"]["checkDups"] = True  #: checkDups flag

                for p_name, p_data in relatedplaylist.items():
                    if self.config.get(p_name):
                        p_data["title"] += " of " + user
                        playlists.append(p_data)
            else:
                playlists = []
        else:
            self.log_debug("Url recognized as Playlist")
            playlists = [self.get_playlist(m_id)]

        if not playlists:
            self.fail(self._("No playlist available"))

        addedvideos = []
        urlize = lambda x: "https://www.youtube.com/watch?v=" + x
        for p in playlists:
            p_name = p["title"]
            p_videos = self.get_videos_id(p["id"])
            p_folder = os.path.join(
                self.pyload.config.get("general", "storage_folder"),
                p["channelTitle"],
                p_name,
            )
            self.log_debug(
                r'{} video\s found on playlist "{}"'.format(len(p_videos), p_name)
            )

            if not p_videos:
                continue
            elif "checkDups" in p:
                p_urls = [urlize(v_id) for v_id in p_videos if v_id not in addedvideos]
                self.log_debug(
                    r'{} video\s available on playlist "{}" after duplicates cleanup'.format(
                        len(p_urls), p_name
                    )
                )
            else:
                p_urls = [urlize(url) for url in p_videos]

            #: Folder is NOT recognized by pyload 0.5.0!
            self.packages.append((p_name, p_urls, p_folder))

            addedvideos.extend(p_videos)
