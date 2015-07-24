# -*- coding: utf-8 -*-

import re
import urlparse

from module.common.json_layer import json_loads
from module.plugins.internal.Crypter import Crypter
from module.utils import save_join as fs_join


class DailymotionComFolder(Crypter):
    __name__    = "DailymotionComFolder"
    __type__    = "crypter"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?dailymotion\.com/((playlists/)?(?P<TYPE>playlist|user)/)?(?P<ID>[\w^_]+)(?(TYPE)|#)'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Dailymotion.com channel & playlist decrypter"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def api_response(self, ref, data=None):
        url  = urlparse.urljoin("https://api.dailymotion.com/", ref)
        html = self.load(url, get=data)
        return json_loads(html)


    def get_playlist_info(self, id):
        ref  = "playlist/" + id
        data = {'fields': "name,owner.screenname"}
        playlist = self.api_response(ref, data)

        if "error" in playlist:
            return

        name = playlist['name']
        owner = playlist['owner.screenname']
        return name, owner


    def _get_playlists(self, user_id, page=1):
        ref  = "user/%s/playlists" % user_id
        data = {'fields': "id", 'page': page, 'limit': 100}
        user = self.api_response(ref, data)

        if "error" in user:
            return

        for playlist in user['list']:
            yield playlist['id']

        if user['has_more']:
            for item in self._get_playlists(user_id, page + 1):
                yield item


    def get_playlists(self, user_id):
        return [(id,) + self.get_playlist_info(id) for id in self._get_playlists(user_id)]


    def _get_videos(self, id, page=1):
        ref  = "playlist/%s/videos" % id
        data = {'fields': "url", 'page': page, 'limit': 100}
        playlist = self.api_response(ref, data)

        if "error" in playlist:
            return

        for video in playlist['list']:
            yield video['url']

        if playlist['has_more']:
            for item in self._get_videos(id, page + 1):
                yield item


    def get_videos(self, playlist_id):
        return list(self._get_videos(playlist_id))[::-1]


    def decrypt(self, pyfile):
        m = re.match(self.__pattern__, pyfile.url)
        m_id = m.group('ID')
        m_type = m.group('TYPE')

        if m_type == "playlist":
            self.log_debug("Url recognized as Playlist")
            p_info = self.get_playlist_info(m_id)
            playlists = [(m_id,) + p_info] if p_info else None
        else:
            self.log_debug("Url recognized as Channel")
            playlists = self.get_playlists(m_id)
            self.log_debug("%s playlist\s found on channel \"%s\"" % (len(playlists), m_id))

        if not playlists:
            self.fail(_("No playlist available"))

        for p_id, p_name, p_owner in playlists:
            p_videos = self.get_videos(p_id)
            p_folder = fs_join(self.pyload.config.get("general", "download_folder"), p_owner, p_name)
            self.log_debug("%s video\s found on playlist \"%s\"" % (len(p_videos), p_name))
            self.packages.append((p_name, p_videos, p_folder))  #: Folder is NOT recognized by pyload 0.4.9!
