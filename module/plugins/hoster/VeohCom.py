# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VeohCom(SimpleHoster):
    __name__ = "VeohCom"
    __type__ = "hoster"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?veoh\.com/(tv/)?(watch|videos)/(?P<ID>v\w+)'
    __config__ = [("quality", "Low;High;Auto", "Quality", "Auto")]

    __description__ = """Veoh.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    FILE_NAME_PATTERN = r'<meta name="title" content="(?P<N>.*?)"'
    OFFLINE_PATTERN = r'>Sorry, we couldn\'t find the video you were looking for'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'http://www.veoh.com/watch/\g<ID>')]

    SH_COOKIES = [(".veoh.com", "lassieLocale", "en")]


    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = -1

    def handleFree(self):
        quality = self.getConfig("quality")
        if quality == "Auto":
            quality = ("High", "Low")
        for q in quality:
            pattern = r'"fullPreviewHash%sPath":"(.+?)"' % q
            m = re.search(pattern, self.html)
            if m:
                self.pyfile.name += ".mp4"
                link = m.group(1).replace("\\", "")
                self.logDebug("Download link: " + link)
                self.download(link)
                return
            else:
                self.logInfo("No %s quality video found" % q.upper())
        else:
            self.fail("No video found!")


getInfo = create_getInfo(VeohCom)
