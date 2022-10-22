# -*- coding: utf-8 -*-
import json
import random
import re

from pyload.core.datatypes.pyfile import status_map
from pyload.core.network.request_factory import get_url

from ..base.downloader import BaseDownloader


def get_info(urls):
    result = []
    m = re.compile(DailymotionCom.__pattern__)

    for url in urls:
        id = m.match(url).group("ID")
        html = get_url(
            "https://api.dailymotion.com/video/{}".format(id),
            get={"fields": "access_error,status,title"},
        )
        info = json.loads(html)

        name = info["title"] + ".mp4" if "title" in info else url

        if "error" in info or info["access_error"]:
            status = "offline"

        else:
            status = info["status"]

            if status in ("ready", "published"):
                status = "online"

            elif status in ("waiting", "processing"):
                status = "temp. offline"

            else:
                status = "offline"

        result.append((name, 0, status_map[status], url))

    return result


class DailymotionCom(BaseDownloader):
    __name__ = "DailymotionCom"
    __type__ = "downloader"
    __version__ = "0.32"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?(?:dailymotion\.com/.*video|dai\.ly)/(?P<ID>[\w^_]+)"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        (
            "quality",
            "Lowest;LD 144p;LD 240p;SD 380p;HQ 480p;HD 720p;HD 1080p;Highest",
            "Quality",
            "Highest",
        ),
    ]

    __description__ = """Dailymotion.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Synology PAT", "pat@synology.com"),
        ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com"),
    ]

    STREAM_PATTERN = r"\"(?P<URL>https?:\\/\\/www.dailymotion.com\\/cdn\\/H264-(?P<QF_WIDTH>\d+)x(?P<QF_HEIGHT>\d+).*?)\""

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def get_info(self, url="", html=""):
        info = super(DailymotionCom, self).get_info(url, html)

        name, size, status, url = get_info([url])[0]

        info.update({"name": name, "status": status})

        return info

    def process(self, pyfile):
        desired_quality = self.config.get("quality")

        self.data = self.load(
            "https://www.dailymotion.com/player/metadata/video/{}".format(
                self.info["pattern"]["ID"]
            )
        )
        json_data = json.loads(self.data)
        m3u8_url = next(iter(json_data["qualities"].values()))[0]["url"]
        m3u8_data = self.load(m3u8_url)

        streams = {}
        for m in re.finditer(r"#EXT-X-STREAM-INF:(.+)", m3u8_data):
            stream = dict(
                [
                    (x.group(1), x.group(2) or x.group(3))
                    for x in re.finditer(
                        r'([\w-]+)=(?:(?=")"([^"]+)|(?!")([^,]+))', m.group(1)
                    )
                ]
            )
            quality = int(stream["NAME"])
            dl_url = stream["PROGRESSIVE-URI"]
            streams[quality] = streams.get(quality, []) + [dl_url]

        if not streams:
            self.fail(self._("Failed to get any streams."))

        qualities = sorted(streams.keys())
        if desired_quality == "Lowest":
            quality = qualities[0]
        elif desired_quality == "Highest":
            quality = qualities[-1]
        else:
            desired_quality = int(re.search(r"\d+", desired_quality).group(0))
            quality = min(qualities, key=lambda x: abs(x - desired_quality))

        self.download(random.choice(streams[quality]))
