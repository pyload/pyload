# -*- coding: utf-8 -*-

import re

from module.plugins.internal.misc import json
from module.plugins.internal.Hoster import Hoster



class HearthisAt(Hoster):
    __name__    = "HearthisAt"
    __type__    = "hoster"
    __version__ = "0.01"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?hearthis\.at/'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Hearthis.at hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001{AT]yahoo{DOT]com")]


    def setup(self):
        self.multiDL = True


    def process(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(r'intTrackId = (\d+);', html)
        if m is None:
            self.fail(_("Track ID not found"))

        track_id = m.group(1)

        data = self.load("https://hearthis.at/playlist.php",
                         post={'tracks[]': track_id})
        json_data = json.loads(data)

        pyfile.name = json_data[0]['title'] + ".mp3"

        self.download(json_data[0]['track_url'])