# -*- coding: utf-8 -*-

import pycurl
import re

from module.plugins.Hoster import Hoster


class SoundcloudCom(Hoster):
    __name__ = "SoundcloudCom"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = r'https?://(?:www\.)?soundcloud\.com/(?P<UID>.*?)/(?P<SID>.*)'

    __description__ = """SoundCloud.com hoster plugin"""
    __author_name__ = "Peekayy"
    __author_mail__ = "peekayy.dev@gmail.com"


    def process(self, pyfile):
        # default UserAgent of HTTPRequest fails for this hoster so we use this one
        self.req.http.c.setopt(pycurl.USERAGENT, 'Mozilla/5.0')
        page = self.load(pyfile.url)
        m = re.search(r'<div class="haudio.*?large.*?" data-sc-track="(?P<ID>[0-9]*)"', page)
        songId = clientId = ""
        if m:
            songId = m.group("ID")
        if len(songId) <= 0:
            self.logError("Could not find song id")
            self.offline()
        else:
            m = re.search(r'"clientID":"(?P<CID>.*?)"', page)
            if m:
                clientId = m.group("CID")

            if len(clientId) <= 0:
                clientId = "b45b1aa10f1ac2941910a7f0d10f8e28"

            m = re.search(r'<em itemprop="name">\s(?P<TITLE>.*?)\s</em>', page)
            if m:
                pyfile.name = m.group("TITLE") + ".mp3"
            else:
                pyfile.name = re.match(self.__pattern__, pyfile.url).group("SID") + ".mp3"

            # url to retrieve the actual song url
            page = self.load("https://api.sndcdn.com/i1/tracks/%s/streams" % songId, get={"client_id": clientId})
            # getting streams
            # for now we choose the first stream found in all cases
            # it could be improved if relevant for this hoster
            streams = [
                (result.group("QUALITY"), result.group("URL"))
                for result in re.finditer(r'"(?P<QUALITY>.*?)":"(?P<URL>.*?)"', page)
            ]
            self.logDebug("Found Streams", streams)
            self.logDebug("Downloading", streams[0][0], streams[0][1])
            self.download(streams[0][1])
