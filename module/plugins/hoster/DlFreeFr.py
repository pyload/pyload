# -*- coding: utf-8 -*-

import pycurl
import re

from module.network.Browser import Browser
from module.network.CookieJar import CookieJar
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo, replace_patterns


class CustomBrowser(Browser):

    def __init__(self, bucket=None, options={}):
        Browser.__init__(self, bucket, options)


    def load(self, *args, **kwargs):
        post = kwargs.get("post")

        if post is None and len(args) > 2:
            post = args[2]

        if post:
            self.http.c.setopt(pycurl.FOLLOWLOCATION, 0)
            self.http.c.setopt(pycurl.POST, 1)
            self.http.c.setopt(pycurl.CUSTOMREQUEST, "POST")
        else:
            self.http.c.setopt(pycurl.FOLLOWLOCATION, 1)
            self.http.c.setopt(pycurl.POST, 0)
            self.http.c.setopt(pycurl.CUSTOMREQUEST, "GET")

        return Browser.load(self, *args, **kwargs)


class DlFreeFr(SimpleHoster):
    __name__    = "DlFreeFr"
    __type__    = "hoster"
    __version__ = "0.32"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?dl\.free\.fr/(\w+|getfile\.pl\?file=/\w+)'
    __config__  = [("use_premium", "bool", "Use premium account if available", True)]

    __description__ = """Dl.free.fr hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("the-razer", "daniel_ AT gmx DOT net"),
                       ("zoidberg" , "zoidberg@mujmail.cz"   ),
                       ("Toilal"   , "toilal.dev@gmail.com"  )]


    NAME_PATTERN    = r'Fichier:</td>\s*<td.*?>(?P<N>[^>]*)</td>'
    SIZE_PATTERN    = r'Taille:</td>\s*<td.*?>(?P<S>[\d.,]+\w)o'
    OFFLINE_PATTERN = r'Erreur 404 - Document non trouv|Fichier inexistant|Le fichier demand&eacute; n\'a pas &eacute;t&eacute; trouv&eacute;'


    def setup(self):
        self.resume_download = True
        self.multiDL        = True
        self.limitDL        = 5
        self.chunk_limit     = 1


    def init(self):
        factory = self.pyload.requestFactory
        self.req = CustomBrowser(factory.bucket, factory.getOptions())


    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)
        valid_url = pyfile.url
        headers = self.load(valid_url, just_header=True)

        if headers.get('code') == 302:
            valid_url = headers.get('location')
            headers = self.load(valid_url, just_header=True)

        if headers.get('code') == 200:
            content_type = headers.get('content-type')
            if content_type and content_type.startswith("text/html"):
                #: Undirect acces to requested file, with a web page providing it (captcha)
                self.html = self.load(valid_url)
                self.handle_free(pyfile)
            else:
                #: Direct access to requested file for users using free.fr as Internet Service Provider.
                self.link = valid_url

            self.download(self.link, disposition=True)

        elif headers.get('code') == 404:
            self.offline()

        else:
            self.fail(_("Invalid return code: ") + str(headers.get('code')))


    def handle_free(self, pyfile):
        action, inputs = self.parse_html_form('action="getfile.pl"')
        self.load("http://dl.free.fr/getfile.pl", post=inputs)
        headers = self.get_last_headers()
        if headers.get("code") == 302 and "set-cookie" in headers and "location" in headers:
            m = re.search("(.*?)=(.*?); path=(.*?); domain=(.*)", headers.get("set-cookie"))
            cj = CookieJar(self.__name__)
            if m:
                cj.setCookie(m.group(4), m.group(1), m.group(2), m.group(3))
            else:
                self.fail(_("Cookie error"))

            self.link = headers.get("location")
            self.req.setCookieJar(cj)
        else:
            self.fail(_("Invalid response"))


    def get_last_headers(self):
        #: Parse header
        header = {'code': self.req.code}
        for line in self.req.http.header.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue

            key, none, value = line.partition(":")
            key = key.lower().strip()
            value = value.strip()

            if key in header:
                if type(header[key]) is list:
                    header[key].append(value)
                else:
                    header[key] = [header[key], value]
            else:
                header[key] = value
        return header


getInfo = create_getInfo(DlFreeFr)
