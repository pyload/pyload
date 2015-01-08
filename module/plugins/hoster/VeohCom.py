# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VeohCom(SimpleHoster):
    __name__    = "VeohCom"
    __type__    = "hoster"
    __version__ = "0.22"

    __pattern__ = r'http://(?:www\.)?veoh\.com/(tv/)?(watch|videos)/(?P<ID>v\w+)'
    __config__ = [("quality", "Low;High;Auto", "Quality", "Auto")]

    __description__ = """Veoh.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<meta name="title" content="(?P<N>.*?)"'
    OFFLINE_PATTERN = r'>Sorry, we couldn\'t find the video you were looking for'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://www.veoh.com/watch/\g<ID>')]

    COOKIES = [("veoh.com", "lassieLocale", "en")]


    def setup(self):
        self.resumeDownload = True
        self.multiDL        = True
        self.chunkLimit     = -1


    def handleFree(self, pyfile):
        quality = self.getConfig("quality")
        if quality == "Auto":
            quality = ("High", "Low")

        for q in quality:
            pattern = r'"fullPreviewHash%sPath":"(.+?)"' % q
            m = re.search(pattern, self.html)
            if m:
                pyfile.name += ".mp4"
                link = m.group(1).replace("\\", "")
                self.download(link)
                return
            else:
                self.logInfo(_("No %s quality video found") % q.upper())
        else:
            self.fail(_("No video found!"))


getInfo = create_getInfo(VeohCom)
