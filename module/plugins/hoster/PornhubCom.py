# -*- coding: utf-8 -*-

import re

from module.network.CookieJar import CookieJar
from module.network.HTTPRequest import HTTPRequest

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster
from ..internal.Plugin import Abort


class BIGHTTPRequest(HTTPRequest):
    """
    Overcome HTTPRequest's load() size limit to allow
    loading very big web pages by overrding HTTPRequest's write() function
    """

    # @TODO: Add 'limit' parameter to HTTPRequest in v0.4.10
    def __init__(self, cookies=None, options=None, limit=1000000):
        self.limit = limit
        HTTPRequest.__init__(self, cookies=cookies, options=options)

    def write(self, buf):
        """ writes response """
        if self.limit and self.rep.tell() > self.limit or self.abort:
            rep = self.getResponse()
            if self.abort:
                raise Abort()
            f = open("response.dump", "wb")
            f.write(rep)
            f.close()
            raise Exception("Loaded Url exceeded limit")

        self.rep.write(buf)


class PornhubCom(SimpleHoster):
    __name__ = "PornhubCom"
    __type__ = "hoster"
    __version__ = "0.60"
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


    @classmethod
    def get_info(cls, url="", html=""):
        info = super(PornhubCom, cls).get_info(url, html)
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
            cookies=CookieJar(None),
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
