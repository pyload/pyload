import re
from xml.etree.ElementTree import fromstring

from module.plugins.Hoster import Hoster

XML_API = "http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?id=%i"


class ZDF(Hoster):
    # Based on zdfm by Roland Beermann
    # http://github.com/enkore/zdfm/
    __name__ = "ZDF Mediathek"
    __version__ = "0.8"
    __pattern__ = r"http://www\.zdf\.de/ZDFmediathek/[^0-9]*([0-9]+)[^0-9]*"
    __config__ = []

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
        return int(re.search(r"[^0-9]*([0-9]{4,})[^0-9]*", url).group(1))

    def process(self, pyfile):
        xml = fromstring(self.load(XML_API % self.get_id(pyfile.url)))

        status = xml.findtext("./status/statuscode")
        if status != "ok":
            self.fail("Error retrieving manifest.")

        video = xml.find("video")
        title = video.findtext("information/title")

        pyfile.name = title

        target_url = sorted((v for v in video.iter("formitaet") if self.video_valid(v)),
                            key=self.video_key)[-1].findtext("url")

        self.download(target_url)
