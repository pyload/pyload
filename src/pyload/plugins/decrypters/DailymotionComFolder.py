# -*- coding: utf-8 -*-

import json
import os
import urllib.parse

from ..base.decrypter import BaseDecrypter


class DailymotionComFolder(BaseDecrypter):
    __name__ = "DailymotionComFolder"
    __type__ = "decrypter"
    __version__ = "0.08"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?dailymotion\.com/((playlists/)?(?P<TYPE>playlist|user)/)?(?P<ID>[\w^_]+)(?(TYPE)|#)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """Dailymotion.com channel & playlist decrypter"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def api_response(self, ref, data=None):
        url = urllib.parse.urljoin("https://api.dailymotion.com/", ref)
        html = self.load(url, get=data)
        return json.loads(html)

    def get_playlist_info(self, id):
        ref = "playlist/" + id
        data = {"fields": "name,owner.screenname"}
        playlist = self.api_response(ref, data)

        if "error" in playlist:
            return

        name = playlist["name"]
        owner = playlist["owner.screenname"]
        return name, owner

    def _get_playlists(self, user_id, page=1):
        ref = "user/{}/playlists".format(user_id)
        data = {"fields": "id", "page": page, "limit": 100}
        user = self.api_response(ref, data)

        if "error" in user:
            return

        for playlist in user["list"]:
            yield playlist["id"]

        if user["has_more"]:
            for item in self._get_playlists(user_id, page + 1):
                yield item

    def get_playlists(self, user_id):
        return [
            (id,) + self.get_playlist_info(id) for id in self._get_playlists(user_id)
        ]

    def _get_videos(self, id, page=1):
        ref = "playlist/{}/videos".format(id)
        data = {"fields": "url", "page": page, "limit": 100}
        playlist = self.api_response(ref, data)

        if "error" in playlist:
            return

        for video in playlist["list"]:
            yield video["url"]

        if playlist["has_more"]:
            for item in self._get_videos(id, page + 1):
                yield item

    def get_videos(self, playlist_id):
        return list(self._get_videos(playlist_id))[::-1]

    def decrypt(self, pyfile):
        m_id = self.info["pattern"]["ID"]
        m_type = self.info["pattern"]["TYPE"]

        if m_type == "playlist":
            self.log_debug("Url recognized as Playlist")
            p_info = self.get_playlist_info(m_id)
            playlists = [(m_id,) + p_info] if p_info else None
        else:
            self.log_debug("Url recognized as Channel")
            playlists = self.get_playlists(m_id)
            self.log_debug(
                r'{} playlist\s found on channel "{}"'.format(len(playlists), m_id)
            )

        if not playlists:
            self.fail(self._("No playlist available"))

        for p_id, p_name, p_owner in playlists:
            p_videos = self.get_videos(p_id)
            p_folder = os.path.join(
                self.pyload.config.get("general", "storage_folder"), p_owner, p_name
            )
            self.log_debug(
                r'{} video\s found on playlist "{}"'.format(len(p_videos), p_name)
            )
            # NOTE: Folder is NOT recognized by pyload 0.5.0!
            self.packages.append((p_name, p_videos, p_folder))
