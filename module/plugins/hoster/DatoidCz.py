# -*- coding: utf-8 -*-

import time
import urlparse

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class DatoidCz(SimpleHoster):
    __name__ = "DatoidCz"
    __type__ = "hoster"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?datoid\.(?:cz|sk|pl)/(?!slozka)\w{6}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Datoid.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = ur'Název souboru: (?P<N>.+)'
    SIZE_PATTERN = r'Velikost: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'Tento soubor neexistuje'

    URL_REPLACEMENTS = [(r'datoid.sk', r'datoid.cz'),
                        (r'datoid.pl', r'datoid.cz')]

    def handle_free(self, pyfile):
        url = self.req.lastEffectiveURL
        urlp = urlparse.urlparse(url)

        json_data = json.loads(self.load(urlparse.urljoin(
            url, "/f/" + urlp.path + str(int(time.time() * 1000)))))
        self.log_debug(json_data)

        if "error" in json_data:
            self.fail(json_data['error'])

        self.link = json_data['redirect']

    def handle_premium(self, pyfile):
        url = self.req.lastEffectiveURL
        urlp = urlparse.urlparse(url)

        self.link = urlparse.urljoin(
            url, "/f/" + urlp.path + str(int(time.time() * 1000)))
