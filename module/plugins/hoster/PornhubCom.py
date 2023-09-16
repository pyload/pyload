# -*- coding: utf-8 -*-

import re

from ..internal.misc import BIGHTTPRequest, json
from ..internal.SimpleHoster import SimpleHoster


class PornhubCom(SimpleHoster):
    __name__ = "PornhubCom"
    __type__ = "hoster"
    __version__ = "0.62"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?pornhub\.com/view_video\.php\?viewkey=\w+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Pornhub.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("jeix", "jeix@hasnomail.de"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'"video_title":"(?P<N>.+?)"'

    TEMP_OFFLINE_PATTERN = r'^unmatchable$'  # Who knows?
    OFFLINE_PATTERN = r'^unmatchable$'  # Who knows?


    def get_info(self, url="", html=""):
        info = super(PornhubCom, self).get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension so we blindly add '.mp4' as an extension.
        # (hopefully all links are '.mp4' files)
        if 'name' in info:
            info['name'] += ".mp4"

        return info

    def setup(self):
        self.resume_download = True
        self.multiDL = True

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.requestFactory.getOptions(),
            limit=2000000)

    def handle_free(self, pyfile):
        m = re.search(r'<div class="video-wrapper">.+?<script type="text/javascript">(.+?)</script>', self.data, re.S)
        if m is None:
            self.error(_("Player Javascript data not found"))

        script = m.group(1)

        m = re.search(r'qualityItems_\d+', script)
        if m is None:
            self.error(_("`qualityItems` variable no found"))

        result_var = re.search(r'qualityItems_\d+', script).group(0)

        script = "".join(re.findall(r'^\s*var .+', script, re.M))
        script = re.sub(r"[\n\t]|/\*.+?\*/", "", script)
        script += "JSON.stringify(%s);" % result_var

        res = self.js.eval(script)
        json_data = json.loads(res)

        urls = dict([(int(re.search("^(\d+)", _x['text']).group(0)), _x['url'])
                     for _x in json_data if _x['url']])

        quality = max(urls.keys())

        self.link = urls[quality]
