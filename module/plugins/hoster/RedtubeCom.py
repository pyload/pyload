# -*- coding: utf-8 -*-

import re

from ..internal.Hoster import Hoster
from ..internal.misc import json


class RedtubeCom(Hoster):
    __name__ = "RedtubeCom"
    __type__ = "hoster"
    __version__ = "0.28"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?redtube\.com/\d+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Redtube.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"),
                   ("GammaC0de", "nitzo2001[AT}yahoo[DOT]com")]

    def process(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(r'playervars: ({.+}),', html)
        if m is None:
            self.error(_("playervars pattern not found"))

        playervars = json.loads(m.group(1))

        media_info = [x["videoUrl"]
                      for x in playervars['mediaDefinitions']
                      if x.get("format") == "mp4" and x.get("remote") is True]
        if len(media_info) == 0:
            self.fail(_("no media definitions found"))

        video_info = json.loads(self.load(media_info[0]))
        video_info = sorted(video_info, key=lambda k: int(k['quality']), reverse=True)

        link = video_info[0]["videoUrl"]

        pyfile.name = playervars['video_title'] + ".mp4"

        self.download(link)
