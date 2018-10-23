# -*- coding: utf-8 -*-

import json
import re
from builtins import _

import js2py

from pyload.core.network.cookie_jar import CookieJar
from pyload.core.network.http_request import HTTPRequest
from pyload.plugins.internal.plugin import Abort
from pyload.plugins.internal.simplehoster import SimpleHoster


class BIGHTTPRequest(HTTPRequest):
    """
    Overcome HTTPRequest's load() size limit to allow loading very big web
    pages by overrding HTTPRequest's write() function.
    """

    # TODO: Add 'limit' parameter to HTTPRequest in v0.6.x
    def __init__(self, cookies=None, options=None, limit=1_000_000):
        self.limit = limit
        super().__init__(cookies=cookies, options=options)

    def write(self, buf):
        """
        writes response.
        """
        if self.limit and self.rep.tell() > self.limit or self.abort:
            rep = self.getResponse()
            if self.abort:
                raise Abort
            with open("response.dump", mode="wb") as f:
                f.write(rep)
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)


class PornhubCom(SimpleHoster):
    __name__ = "PornhubCom"
    __type__ = "hoster"
    __version__ = "0.60"
    __status__ = "testing"

    __pyload_version__ = "0.5"

    __pattern__ = r"https?://(?:www\.)?pornhub\.com/view_video\.php\?viewkey=\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Pornhub.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    NAME_PATTERN = r'"video_title":"(?P<N>.+?)"'

    TEMP_OFFLINE_PATTERN = r"^unmatchable$"  #: Who knows?
    OFFLINE_PATTERN = r"^unmatchable$"  #: Who knows?

    @classmethod
    def get_info(cls, url="", html=""):
        info = super(PornhubCom, cls).get_info(url, html)
        # Unfortunately, NAME_PATTERN does not include file extension so we blindly add '.mp4' as an extension.
        # (hopefully all links are '.mp4' files)
        if "name" in info:
            info["name"] += ".mp4"

        return info

    def setup(self):
        self.resume_download = True
        self.multiDL = True

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=CookieJar(None),
            options=self.pyload.requestFactory.getOptions(),
            limit=2_000_000,
        )

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

        res = js2py.eval_js(script)
        json_data = json.loads(res)

        urls = {
            int(re.search("^(\d+)", x["text"]).group(0)): x["url"]
            for x in json_data
            if x["url"]
        }

        quality = max(urls.keys())

        self.link = urls[quality]
