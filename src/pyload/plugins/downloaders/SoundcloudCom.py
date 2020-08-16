# -*- coding: utf-8 -*-
import json
import re

from ..base.simple_downloader import SimpleDownloader


class SoundcloudCom(SimpleDownloader):
    __name__ = "SoundcloudCom"
    __type__ = "downloader"
    __version__ = "0.18"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?soundcloud\.com/[\w\-]+/[\w\-]+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """SoundCloud.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'title" content="(?P<N>.+?)"'
    OFFLINE_PATTERN = r'<title>"SoundCloud - Hear the world’s sounds"</title>'

    def handle_free(self, pyfile):
        try:
            song_id = re.search(r'sounds:(\d+)"', self.data).group(1)

        except Exception:
            self.error(self._("Could not find song id"))

        try:
            script = re.search(
                r'<script(?:\s+[^>]+|\s+)src=(["\'])([^>]*/app-[^>]*\.js)\1', self.data
            ).group(2)
            self.data = self.load(script)
            client_id = re.search(
                r'\Wclient_id\s*:\s*(["\'])(\w+?)\1', self.data
            ).group(2)

        except (AttributeError, IndexError):
            self.fail("Failed to retrieve client_id")

        #: Url to retrieve the actual song url
        html = self.load(
            "https://api.soundcloud.com/tracks/{}/streams".format(song_id),
            get={"client_id": client_id},
        )
        streams = json.loads(html)

        _re = re.compile(r"[^\d]")
        http_streams = sorted(
            [(key, value) for key, value in streams.items() if key.startswith("http_")],
            key=lambda t: _re.sub(t[0], ""),
            reverse=True,
        )

        self.log_debug(f"Streams found: {http_streams or None}")

        if http_streams:
            stream_name, self.link = http_streams[
                0 if self.config.get("quality") == "Higher" else -1
            ]
            pyfile.name += ".{}".format(stream_name.split("_")[1].lower())
