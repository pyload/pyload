# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VeohCom(SimpleHoster):
    __name__    = "VeohCom"
    __type__    = "hoster"
    __version__ = "0.23"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?veoh\.com/(tv/)?(watch|videos)/(?P<ID>v\w+)'
    __config__  = [("use_premium", "bool"         , "Use premium account if available", True  ),
                   ("quality"    , "Low;High;Auto", "Quality"                         , "Auto")]

    __description__ = """Veoh.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'<meta name="title" content="(?P<N>.*?)"'
    OFFLINE_PATTERN = r'>Sorry, we couldn\'t find the video you were looking for'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://www.veoh.com/watch/\g<ID>')]

    COOKIES = [("veoh.com", "lassieLocale", "en")]


    def setup(self):
        self.resume_download = True
        self.multiDL        = True
        self.chunk_limit     = -1


    def handle_free(self, pyfile):
        quality = self.get_config('quality')
        if quality == "Auto":
            quality = ("High", "Low")

        for q in quality:
            pattern = r'"fullPreviewHash%sPath":"(.+?)"' % q
            m = re.search(pattern, self.html)
            if m:
                pyfile.name += ".mp4"
                self.link = m.group(1).replace("\\", "")
                return
            else:
                self.log_info(_("No %s quality video found") % q.upper())
        else:
            self.fail(_("No video found!"))


getInfo = create_getInfo(VeohCom)
