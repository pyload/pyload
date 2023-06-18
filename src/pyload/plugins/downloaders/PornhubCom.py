# -*- coding: utf-8 -*-

import json
import re

from pyload.core.utils.misc import eval_js

from ..base.simple_downloader import SimpleDownloader


class PornhubCom(SimpleDownloader):
    __name__ = "PornhubCom"
    __type__ = "downloader"
    __version__ = "0.62"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?pornhub\.com/view_video\.php\?viewkey=\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Pornhub.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'"video_title":"(?P<N>.+?)"'

    TEMP_OFFLINE_PATTERN = r"^unmatchable$"  #: Who knows?
    OFFLINE_PATTERN = r"^unmatchable$"  #: Who knows?

    def get_info(self, url="", html=""):
        info = super(PornhubCom, self).get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension so we blindly add '.mp4' as an extension.
        # (hopefully all links are '.mp4' files)
        if "name" in info:
            info["name"] += ".mp4"

        return info

    def setup(self):
        self.resume_download = True
        self.multi_dl = True

    def handle_free(self, pyfile):
        m = re.search(
            r'<div class="video-wrapper">.+?<script type="text/javascript">(.+?)</script>',
            self.data,
            re.S,
        )
        if m is None:
            self.error(self._("Player Javascript data not found"))

        script = m.group(1)

        m = re.search(r"qualityItems_\d+", script)
        if m is None:
            self.error(self._("`qualityItems` variable no found"))

        result_var = re.search(r"qualityItems_\d+", script).group(0)

        script = "".join(re.findall(r"^\s*var .+", script, re.M))
        script = re.sub(r"[\n\t]|/\*.+?\*/", "", script)
        script += "JSON.stringify({});".format(result_var)

        res = eval_js(script)
        json_data = json.loads(res)

        urls = {
            int(re.search(r"^(\d+)", x["text"]).group(0)): x["url"]
            for x in json_data
            if x["url"]
        }

        quality = max(urls.keys())

        self.link = urls[quality]
