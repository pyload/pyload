# -*- coding: utf-8 -*-

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class VimeoCom(SimpleHoster):
    __name__ = "VimeoCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(player\.)?vimeo\.com/(video/)?(?P<ID>\d+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int",
                   "Reconnect if waiting time is greater than minutes", 10),
                  ("quality", "Lowest;360p;540p;720p;1080p;Highest", "Quality", "Highest")]

    __description__ = """Vimeo.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'<title>(?P<N>.+?) on Vimeo<'
    OFFLINE_PATTERN = r'class="exception_header"'
    TEMP_OFFLINE_PATTERN = r'Please try again in a few minutes.<'

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'https://www.vimeo.com/\g<ID>')]

    COOKIES = [("vimeo.com", "language", "en")]

    @classmethod
    def get_info(cls, url="", html=""):
        info = SimpleHoster.get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension so we blindly add '.mp4' as an extension.
        # (hopefully all links are '.mp4' files)
        if 'name' in info:
            info['name'] += ".mp4"

        return info

    def setup(self):
        self.resume_download = True
        self.multiDL = True
        self.chunk_limit = -1

    def handle_free(self, pyfile):
        json_data = self.load(
            "https://player.vimeo.com/video/%s/config" %
            self.info['pattern']['ID'])

        if not json_data.startswith('{'):
            self.fail(_("Unexpected response, expected JSON data"))

        json_data = json.loads(json_data)

        videos = dict((v['quality'], v['url'])
                      for v in json_data['request']['files']['progressive'])

        quality = self.config.get('quality')
        if quality == "Highest":
            qlevel = ("1080p", "720p", "540p", "360p")

        elif quality == "Lowest":
            qlevel = ("360p", "540p", "720p", "1080p")

        else:
            qlevel = quality

        for q in qlevel:
            if q in videos.keys():
                self.link = videos[q]
                return

            else:
                self.log_info(_("No %s quality video found") % q)
        else:
            self.fail(_("No video found!"))
