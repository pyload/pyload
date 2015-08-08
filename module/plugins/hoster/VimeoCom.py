# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VimeoCom(SimpleHoster):
    __name__    = "VimeoCom"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(player\.)?vimeo\.com/(video/)?(?P<ID>\d+)'
    __config__  = [("use_premium", "bool"                       , "Use premium account if available" , True     ),
                   ("quality"    , "Lowest;Mobile;SD;HD;Highest", "Quality"                          , "Highest"),
                   ("original"   , "bool"                       , "Try to download the original file", True     )]

    __description__ = """Vimeo.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN         = r'<title>(?P<N>.+?) on Vimeo<'
    OFFLINE_PATTERN      = r'class="exception_header"'
    TEMP_OFFLINE_PATTERN = r'Please try again in a few minutes.<'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'https://www.vimeo.com/\g<ID>')]

    COOKIES = [("vimeo.com", "language", "en")]


    def setup(self):
        self.resume_download = True
        self.multiDL        = True
        self.chunk_limit     = -1


    def handle_free(self, pyfile):
        password = self.get_password()

        if self.js and 'class="btn iconify_down_b"' in self.html:
            html    = self.js.eval(self.load(pyfile.url, get={'action': "download", 'password': password}))
            pattern = r'href="(?P<URL>http://vimeo\.com.+?)".*?\>(?P<QL>.+?) '
        else:
            html    = self.load("https://player.vimeo.com/video/" + self.info['pattern']['ID'], get={'password': password})
            pattern = r'"(?P<QL>\w+)":{"profile".*?"(?P<URL>http://pdl\.vimeocdn\.com.+?)"'

        link = dict((l.group('QL').lower(), l.group('URL')) for l in re.finditer(pattern, html))

        if self.get_config('original'):
            if "original" in link:
                self.link = link[q]
                return
            else:
                self.log_info(_("Original file not downloadable"))

        quality = self.get_config('quality')
        if quality == "Highest":
            qlevel = ("hd", "sd", "mobile")
        elif quality == "Lowest":
            qlevel = ("mobile", "sd", "hd")
        else:
            qlevel = quality.lower()

        for q in qlevel:
            if q in link:
                self.link = link[q]
                return
            else:
                self.log_info(_("No %s quality video found") % q.upper())
        else:
            self.fail(_("No video found!"))


getInfo = create_getInfo(VimeoCom)
