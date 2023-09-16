# -*- coding: utf-8 -*-

import re

from ..internal.misc import BIGHTTPRequest, json
from ..internal.SimpleHoster import SimpleHoster


class SoundcloudCom(SimpleHoster):
    __name__ = "SoundcloudCom"
    __type__ = "hoster"
    __version__ = "0.22"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?soundcloud\.com/[\w\-]+/[\w\-]+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """SoundCloud.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'title" content="(?P<N>.+?)"'
    OFFLINE_PATTERN = r'<title>"SoundCloud - Hear the world’s sounds"</title>'

    def setup(self):
        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.requestFactory.getOptions(),
            limit=5000000,
        )

    def get_info(self, url="", html=""):
        info = super(SoundcloudCom, self).get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension, so we add '.mp3' as an extension.
        if "name" in info:
            info["name"] += ".mp3"

        return info

    def handle_free(self, pyfile):
        try:
            json_data = re.search(
                r"<script>window\.__sc_hydration = (.+?);</script>", self.data
            ).group(1)

        except (AttributeError, IndexError):
            self.fail("Failed to retrieve json_data")

        try:
            js_url = re.findall(r'script crossorigin src="(.+?)"></script>', self.data)[-1]
        except IndexError:
            self.fail(_("Failed to find js_url"))

        js_data = self.load(js_url)
        m = re.search(r'[ ,]client_id:"(.+?)"', js_data)
        if m is None:
            self.fail(_("client_id not found"))

        client_id = m.group(1)

        hydra_table = dict([(table["hydratable"], table["data"]) for table in json.loads(json_data)])
        streams = [s["url"]
                   for s in hydra_table["sound"]["media"]["transcodings"]
                   if s["format"]["protocol"] == "progressive" and s["format"]["mime_type"] == "audio/mpeg"]
        track_authorization = hydra_table["sound"]["track_authorization"]

        if streams:
            json_data = self.load(streams[0],
                                  get={"client_id": client_id,
                                       "track_authorization": track_authorization})
            self.link = json.loads(json_data).get("url")
