# -*- coding: utf-8 -*-

############################################################################
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  @author: Walter Purcaro
############################################################################


import re

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster
from module.PyFile import statusMap


def getInfo(urls):
    result = []  #: [ .. (name, size, status, url) .. ]
    regex = re.compile(DailymotionCom.__pattern__)
    apiurl = "https://api.dailymotion.com/video/"
    request = {"fields": "access_error,status,title"}
    for url in urls:
        id = regex.search(url).group("ID")
        page = getURL(apiurl + id, get=request)
        info = json_loads(page)

        if "title" in info:
            name = info["title"] + ".mp4"
        else:
            name = url

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

        result.append((name, 0, statusMap[status], url))
    return result


class DailymotionCom(Hoster):
    __name__ = "DailymotionCom"
    __type__ = "hoster"
    __pattern__ = r"https?://(?:www\.)?dailymotion\.com/.*?video/(?P<ID>[\w^_]+)"
    __version__ = "0.2"
    __config__ = [("quality", "Lowest;LD 144p;LD 240p;SD 384p;HQ 480p;HD 720p;HD 1080p;Highest", "Quality", "HD 720p")]
    __description__ = """Dailymotion Video Download Hoster"""
    __author_name__ = ("Walter Purcaro")
    __author_mail__ = ("vuolter@gmail.com")

    def setup(self):
        self.resumeDownload = self.multiDL = True

    def getStreams(self):
        streams = []
        for result in re.finditer(r"\"(?P<URL>http:\\/\\/www.dailymotion.com\\/cdn\\/H264-(?P<QF>.*?)\\.*?)\"",
                                  self.html):
            url = result.group("URL")
            qf = result.group("QF")
            link = url.replace("\\", "")
            quality = tuple(int(x) for x in qf.split("x"))
            streams.append((quality, link))
        return sorted(streams, key=lambda x: x[0][::-1])

    def getQuality(self):
        q = self.getConfig("quality")
        if q == "Lowest":
            quality = 0
        elif q == "Highest":
            quality = -1
        else:
            quality = int(q.rsplit(" ")[1][:-1])
        return quality

    def getLink(self, streams, quality):
        if quality > 0:
            for x, s in reversed([item for item in enumerate(streams)]):
                qf = s[0][1]
                if qf <= quality:
                    idx = x
                    break
            else:
                idx = 0
        else:
            idx = quality

        s = streams[idx]
        self.logInfo("Download video quality %sx%s" % s[0])
        return s[1]

    def checkInfo(self, pyfile):
        pyfile.name, pyfile.size, pyfile.status, pyfile.url = getInfo([pyfile.url])[0]
        if pyfile.status == 1:
            self.offline()
        elif pyfile.status == 6:
            self.tempOffline()

    def process(self, pyfile):
        self.checkInfo(pyfile)

        id = re.match(self.__pattern__, pyfile.url).group("ID")
        self.html = self.load("http://www.dailymotion.com/embed/video/" + id, decode=True)

        streams = self.getStreams()
        quality = self.getQuality()
        link = self.getLink(streams, quality)

        self.download(link)
