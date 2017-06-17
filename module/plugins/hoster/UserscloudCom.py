# -*- coding: utf-8 -*-

import re

from module.network.CookieJar import CookieJar
from module.network.HTTPRequest import HTTPRequest

from ..internal.SimpleHoster import SimpleHoster


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


class UserscloudCom(SimpleHoster):
    __name__ = "UserscloudCom"
    __type__ = "hoster"
    __version__ = "0.09"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?userscloud\.com/(?P<ID>\w{12})'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Userscloud.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN = r'<a href="https://userscloud.com/.+?" target="_blank">(?P<N>.+?) - (?P<S>[\d.,]+) (?P<U>[\w^_]+)</a>'
    OFFLINE_PATTERN = r'The file you are trying to download is no longer available'
    LINK_FREE_PATTERN = r'<a href="(https://\w+\.usercdn\.com.+?)"'

    URL_REPLACEMENTS = [(__pattern__ + '.*', r'https://userscloud.com/\g<ID>')]

    def setup(self):
        self.multiDL = True
        self.resume_download = False
        self.chunk_limit = 1

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = BIGHTTPRequest(
            cookies=CookieJar(None),
            options=self.pyload.requestFactory.getOptions(),
            limit=300000)


    def handle_free(self, pyfile):
        url, inputs = self.parse_html_form('name="F1"')
        if not inputs:
            return

        self.data = self.load(pyfile.url, post=inputs)

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.link = m.group(1)

