# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VimeoCom(SimpleHoster):
    __name__ = "VimeoCom"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?(player\.)?vimeo\.com/(video/)?(?P<ID>\d+)'
    __config__ = [("quality", "Lowest;Mobile;SD;HD;Highest", "Quality", "Highest"),
                  ("original", "bool", "Try to download the original file first", True)]

    __description__ = """Vimeo.com hoster plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    FILE_NAME_PATTERN = r'<title>(?P<N>.+) on Vimeo<'
    OFFLINE_PATTERN = r'class="exception_header"'
    TEMP_OFFLINE_PATTERN = r'Please try again in a few minutes.<'

    FILE_URL_REPLACEMENTS = [(__pattern__, r'https://www.vimeo.com/\g<ID>')]

    SH_COOKIES = [(".vimeo.com", "language", "en")]


    def setup(self):
        self.resumeDownload = self.multiDL = True
        self.chunkLimit = -1

    def handleFree(self):
        if self.js and 'class="btn iconify_down_b"' in self.html:
            html = self.js.eval(self.load(self.pyfile.url, get={'action': "download"}, decode=True))
            pattern = r'href="(?P<URL>http://vimeo\.com.+?)".*?\>(?P<QL>.+?) '
        else:
            id = re.match(self.__pattern__, self.pyfile.url).group("ID")
            html = self.load("https://player.vimeo.com/video/" + id)
            pattern = r'"(?P<QL>\w+)":{"profile".*?"(?P<URL>http://pdl\.vimeocdn\.com.+?)"'

        link = dict([(l.group('QL').lower(), l.group('URL')) for l in re.finditer(pattern, html)])

        if self.getConfig("original"):
            if "original" in link:
                self.download(link[q])
                return
            else:
                self.logInfo("Original file not downloadable")

        quality = self.getConfig("quality")
        if quality == "Highest":
            qlevel = ("hd", "sd", "mobile")
        elif quality == "Lowest":
            qlevel = ("mobile", "sd", "hd")
        else:
            qlevel = quality.lower()

        for q in qlevel:
            if q in link:
                self.download(link[q])
                return
            else:
                self.logInfo("No %s quality video found" % q.upper())
        else:
            self.fail("No video found!")


getInfo = create_getInfo(VimeoCom)
