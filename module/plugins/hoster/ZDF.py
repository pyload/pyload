# -*- coding: utf-8 -*-

import re
import xml.etree.ElementTree as etree

from module.plugins.internal.Hoster import Hoster


# Based on zdfm by Roland Beermann (http://github.com/enkore/zdfm/)
class ZDF(Hoster):
    __name__    = "ZDF Mediathek"
    __type__    = "hoster"
    __version__ = "0.88"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?zdf\.de/ZDFmediathek/\D*(\d+)\D*'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """ZDF.de hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = []

    XML_API = "http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?id=%i"


    @staticmethod
    def video_key(video):
        return (
            int(video.findtext("videoBitrate", "0")),
            any(f.text == "progressive" for f in video.iter("facet")),
        )


    @staticmethod
    def video_valid(video):
        return video.findtext("url").startswith("http") and video.findtext("url").endswith(".mp4") and \
               video.findtext("facets/facet").startswith("progressive")


    @staticmethod
    def get_id(url):
        return int(re.search(r'\D*(\d{4,})\D*', url).group(1))


    def process(self, pyfile):
        xml = etree.fromstring(self.load(self.XML_API % self.get_id(pyfile.url), decode=False))

        status = xml.findtext("./status/statuscode")
        if status != "ok":
            self.fail(_("Error retrieving manifest"))

        video = xml.find("video")
        title = video.findtext("information/title")

        pyfile.name = title.encode('ascii', errors='replace')

        target_url = sorted((v for v in video.iter("formitaet") if self.video_valid(v)),
                            key=self.video_key)[-1].findtext("url")

        self.download(target_url)
