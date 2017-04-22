# -*- coding: utf-8 -*-

import base64
import re
import urllib

from module.network.RequestFactory import getURL as get_url

from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


def xor_decrypt(data, key):
    data = base64.b64decode(data)
    return "".join(map(lambda x: chr(ord(x[1]) ^ ord(key[x[0] % len(key)])), [
                   (i, c) for i, c in enumerate(data)]))


class MegadyskPl(SimpleHoster):
    __name__ = "MegadyskPl"
    __type__ = "hoster"
    __version__ = "0.04"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?megadysk\.pl/dl/.+'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool",
                   "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Megadysk.pl hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'data-reactid="25">(?P<N>.+?)<'
    SIZE_PATTERN = r'<!-- react-text: 40 -->(?P<S>[\d.,]+)(?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'(?:Nothing has been found|have been deleted)<'

    @classmethod
    def api_info(cls, url):
        html = get_url(url)
        info = {}

        m = re.search(r"window\['.*?'\]\s*=\s*\"(.*?)\"", html)
        if m is None:
            info['status'] = 8
            info['error'] = _("Encrypted info pattern not found")
            return info

        encrypted_info = m.group(1)

        html = get_url("https://megadysk.pl/dist/index.js")

        m = re.search(r't.ISK\s*=\s*"(\w+)"', html)
        if m is None:
            info['status'] = 8
            info['error'] = _("Encryption key pattern not found")
            return info

        key = m.group(1)

        res = xor_decrypt(encrypted_info, key)
        json_data = json.loads(urllib.unquote(res))

        if json_data['app']['maintenance']:
            info['status'] = 6
            return info

        if json_data['app']['downloader'] is None or json_data[
                'app']['downloader']['file']['deleted']:
            info['status'] = 1
            return info

        info['name'] = json_data['app']['downloader']['file']['name']
        info['size'] = json_data['app']['downloader']['file']['size']
        info['download_url'] = json_data['app']['downloader']['url']

        return info

    def setup(self):
        self.multiDL = True
        self.resume_download = False
        self.chunk_limit = 1

    def handle_free(self, pyfile):
        if 'download_url' not in self.info:
            self.error(_("Missing JSON data"))

        self.link = self.fixurl(self.info['download_url'])
