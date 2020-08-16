# -*- coding: utf-8 -*-
import json
import re

from pyload.core.datatypes.pyfile import status_map
from pyload.core.network.request_factory import get_url

from ..base.downloader import BaseDownloader


def get_info(urls):
    result = []
    _re = re.compile(DailymotionCom.__pattern__)
    apiurl = "https://api.dailymotion.com/video/{}"
    request = {"fields": "access_error,status,title"}

    for url in urls:
        id = _re.match(url).group("ID")
        html = get_url(apiurl.format(id), get=request)
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
    __version__ = "0.30"
    __status__ = "testing"

    __pattern__ = (
        r"https?://(?:www\.)?(dailymotion\.com/.*video|dai\.ly)/(?P<ID>[\w^_]+)"
    )
    __config__ = [
        ("enabled", "bool", "Activated", True),
        (
            "quality",
            "Lowest;LD 144p;LD 240p;SD 384p;HQ 480p;HD 720p;HD 1080p;Highest",
            "Quality",
            "Highest",
        ),
    ]

    __description__ = """Dailymotion.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("Synology PAT", "pat@synology.com"),
    ]

    STREAM_PATTERN = r"\"(?P<URL>https?:\\/\\/www.dailymotion.com\\/cdn\\/H264-(?P<QF_WIDTH>\d+)x(?P<QF_HEIGHT>\d+).*?)\""

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def get_streams(self):
        streams = []

        for result in re.finditer(self.STREAM_PATTERN, self.data):
            url = result.group("URL")
            qf_width = result.group("QF_WIDTH")
            qf_height = result.group("QF_HEIGHT")

            link = url.replace("\\", "")
            quality = (int(qf_width), int(qf_height))

            streams.append((quality, link))

        return sorted(streams, key=lambda x: x[0][::-1])

    def get_quality(self):
        q = self.config.get("quality")

        if q == "Lowest":
            quality = 0
        elif q == "Highest":
            quality = -1
        else:
            quality = int(q.rsplit(" ")[1][:-1])

        return quality

    def get_link(self, streams, quality):
        if quality > 0:
            for x, s in [item for item in enumerate(streams)][::-1]:
                qf = s[0][1]
                if qf <= quality:
                    idx = x
                    break
            else:
                idx = 0
        else:
            idx = quality

        s = streams[idx]

        self.log_info(self._("Download video quality {}x{}").format(s[0]))

        return s[1]

    def check_info(self, pyfile):
        pyfile.name, pyfile.size, pyfile.status, pyfile.url = get_info([pyfile.url])[0]

        if pyfile.status == 1:
            self.offline()

        elif pyfile.status == 6:
            self.temp_offline()

    def process(self, pyfile):
        self.check_info(pyfile)

        id = re.match(self.__pattern__, pyfile.url).group("ID")
        self.data = self.load("http://www.dailymotion.com/embed/video/" + id)

        streams = self.get_streams()
        quality = self.get_quality()

        if not streams:
            self.fail(self._("Failed to get any streams."))

        self.download(self.get_link(streams, quality))
