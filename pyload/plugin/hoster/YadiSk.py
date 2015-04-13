# -*- coding: utf-8 -*-

import random
import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster
from pyload.utils import json_loads


class YadiSk(SimpleHoster):
    __name    = "YadiSk"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'https?://yadi\.sk/d/\w+'

    __description = """Yadi.sk hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("GammaC0de", None)]


    OFFLINE_PATTERN = r'Nothing found'


    def setup(self):
        self.resumeDownload = False
        self.multiDL        = False
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        m = re.search(r'<script id="models-client" type="application/json">(.+?)</script>', self.html)
        if m is None:
            self.error(_("could not find required json data"))

        res = json_loads(m.group(1))

        yadisk_ver  = None
        yadisk_sk   = None
        yadisk_id   = None
        yadisk_size = None
        yadisk_name = None

        try:  #@TODO: Copy to apiInfo
            for sect in res:
                if 'model' in sect:
                    if sect['model'] == "config":
                        yadisk_ver = sect['data']['version']
                        yadisk_sk  = sect['data']['sk']

                    elif sect['model'] == "resource":
                        yadisk_id   = sect['data']['id']
                        yadisk_size = sect['data']['meta']['size']
                        yadisk_name = sect['data']['name']

        except Exception, e:
            self.fail(_("Unexpected server response"), e)

        if None in (yadisk_id, yadisk_sk, yadisk_id, yadisk_size, yadisk_name):
           self.error(_("Missing JSON data"))

        self.pyfile.size = yadisk_size
        self.pyfile.name = yadisk_name

        yadisk_idclient = ""
        for _i in range(32):
            yadisk_idclient += random.choice('0123456abcdef')

        try:
            self.html = self.load("https://yadi.sk/models/",
                                  get={'_m': "do-get-resource-url"},
                                  post={'idClient': yadisk_idclient,
                                        'version' : yadisk_ver,
                                        '_model.0': "do-get-resource-url",
                                        'sk'      : yadisk_sk,
                                        'id.0'    : yadisk_id})

            self.link = json_loads(self.html)['models'][0]['data']['file']

        except Exception:
            pass
