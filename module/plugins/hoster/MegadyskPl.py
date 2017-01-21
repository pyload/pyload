# -*- coding: utf-8 -*-

import base64
import urllib
import re

from module.plugins.internal.misc import json
from module.plugins.internal.SimpleHoster import SimpleHoster

class MegadyskPl(SimpleHoster):
    __name__    = "MegadyskPl"
    __type__    = "hoster"
    __version__ = "0.01"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?megadysk\.pl/(?:f|s)/.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Megadysk.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    NAME_PATTERN = r'data-reactid="30">(?P<N>.+?)<'
    SIZE_PATTERN = r'<!-- react-text: 40 -->(?P<S>[\d.,]+)(?P<U>[\w^_]+)'

    OFFLINE_PATTERN = r'(?:Nothing has been found|have been deleted)<'


    def setup(self):
        self.multiDL         = True
        self.resume_download = False
        self.chunk_limit     = 1

    def handle_free(self, pyfile):
        m = re.search(r"window\['.*?'\]\s*=\s*\"(.*?)\"", self.data)
        if m is None:
            self.fail(_("Encrypted info 1 not found"))

        encrypted_info = m.group(1)

        self.data = self.load("https://megadysk.pl/dist/index.js")

        m = re.search(r't.ISK\s*=\s*"(\w+)"', self.data)
        if m is None:
            self.fail(_("Encryption key not found"))

        key = m.group(1)

        data = self.xor_decrypt(encrypted_info , key)
        json_data = json.loads(urllib.unquote(data))

        if json_data['app']['maintenance']:
            self.temp_offline()

        if json_data['app']['folderView']['notFound']:
            self.offline()

        self.data = self.load(self.fixurl(json_data['app']['folderView']['entities'][0]['downloadUrl']))

        m = re.search(r"window\['.*?'\]\s*=\s*\"(.*?)\"", self.data)
        if m is None:
            self.fail(_("Encrypted info 2 not found"))

        encrypted_info = m.group(1)

        data = self.xor_decrypt(encrypted_info , key)
        json_data = json.loads(urllib.unquote(data))

        self.link = self.fixurl(json_data['app']['downloader']['url'])


    def xor_decrypt(self, data, key):
        data = base64.b64decode(data)
        return "".join(map(lambda x: chr(ord(x[1]) ^ ord(key[x[0] % len(key)])), [(i,c) for i,c in enumerate(data)]))
