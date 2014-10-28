# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class NowVideoAt(SimpleHoster):
    __name__    = "NowVideoAt"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?nowvideo\.(at|ch|co|eu|sx)/(video|mobile/#/videos)/(?P<ID>\w+)'

    __description__ = """NowVideo.at hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.nowvideo.at/video/\g<ID>')]

    FILE_NAME_PATTERN = r'<h4>(?P<N>.+?)<'
    OFFLINE_PATTERN = r'>This file no longer exists'

    LINK_PATTERN = r'<source src="(.+?)"'


    def handleFree(self):
        self.html = self.load("http://www.nowvideo.at/mobile/video.php", get={'id': self.file_info['ID']})

        m = re.search(self.LINK_PATTERN, self.html)
        if m is None:
            self.error(_("Download link not found"))

        self.download(m.group(1), disposition=True)


getInfo = create_getInfo(NowVideoAt)
