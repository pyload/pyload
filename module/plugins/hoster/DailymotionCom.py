# -*- coding: utf-8 -*-

import re

from module.PyFile import statusMap
from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.plugins.Hoster import Hoster


def getInfo(urls):
    result  = []
    regex   = re.compile(DailymotionCom.__pattern__)
    apiurl  = "https://api.dailymotion.com/video/%s"
    request = {"fields": "access_error,status,title"}

    for url in urls:
        id   = regex.match(url).group('ID')
        html = getURL(apiurl % id, get=request)
        info = json_loads(html)

        name = info['title'] + ".mp4" if "title" in info else url

        if "error" in info or info['access_error']:
            status = "offline"
        else:
            status = info['status']
            if status in ("ready", "published"):
                status = "online"
            elif status in ("waiting", "processing"):
                status = "temp. offline"
            else:
                status = "offline"

        result.append((name, 0, statusMap[status], url))

    return result


class DailymotionCom(Hoster):
    __name__    = "DailymotionCom"
    __type__    = "hoster"
    __version__ = "0.20"

    __pattern__ = r'https?://(?:www\.)?dailymotion\.com/.*video/(?P<ID>[\w^_]+)'
    __config__  = [("quality", "Lowest;LD 144p;LD 240p;SD 384p;HQ 480p;HD 720p;HD 1080p;Highest", "Quality", "Highest")]

    __description__ = """Dailymotion.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True


    def getStreams(self):
        streams = []

        for result in re.finditer(r"\"(?P<URL>http:\\/\\/www.dailymotion.com\\/cdn\\/H264-(?P<QF>.*?)\\.*?)\"",
                                  self.html):
            url = result.group('URL')
            qf  = result.group('QF')

            link    = url.replace("\\", "")
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

        self.logInfo(_("Download video quality %sx%s") % s[0])

        return s[1]


    def checkInfo(self, pyfile):
        pyfile.name, pyfile.size, pyfile.status, pyfile.url = getInfo([pyfile.url])[0]

        if pyfile.status == 1:
            self.offline()

        elif pyfile.status == 6:
            self.tempOffline()


    def process(self, pyfile):
        self.checkInfo(pyfile)

        id = re.match(self.__pattern__, pyfile.url).group('ID')
        self.html = self.load("http://www.dailymotion.com/embed/video/" + id, decode=True)

        streams = self.getStreams()
        quality = self.getQuality()

        self.download(self.getLink(streams, quality))
