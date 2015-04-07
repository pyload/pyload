# -*- coding: utf-8 -*-

import re
import pycurl
import random

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class YadiSk(SimpleHoster):
    __name__    = "YadiSk"
    __type__    = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://yadi\.sk/d/\w+'

    __description__ = """Yadi.sk hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nomail@fakemailbox.com")]


    OFFLINE_PATTERN = r'Nothing found'


    def setup(self):
        self.resumeDownload = False
        self.multiDL        = False
        self.chunkLimit     = 1


    def handleFree(self, pyfile):
        m = re.search(r'<script id="models-client" type="application/json">(.+?)</script>', self.html)
        if m is None:
            self.fail(_("could not find required json data"))

        res = json_loads(m.group(1))

        yadisk_ver  = None
        yadisk_sk   = None
        yadisk_id   = None
        yadisk_size = None
        yadisk_name = None
        yadisk_hash = None
        try:  #@TODO: Copy to apiInfo method
            for sect in res:
                if 'model' in sect:
                    if sect['model'] == 'config':
                        yadisk_ver = sect['data']['version']
                        yadisk_sk  = sect['data']['sk']

                    elif sect['model'] == 'resource':
                        yadisk_id   = sect['data']['id']
                        yadisk_size = sect['data']['meta']['size']
                        yadisk_name = sect['data']['name']

        except Exception:
            self.fail(_("Unexpected server response"))

        if None is in (yadisk_id, yadisk_sk, yadisk_id, yadisk_size, yadisk_name):
           self.fail(_("json data is missing important information, cannot continue"))

        self.pyfile.size = yadisk_size
        self.pyfile.name = yadisk_name

        yadisk_idclient = ""
        for _i in range(1, 32):
            yadisk_idclient += random.choice('0123456abcdef')

        result_json = self.load("https://yadi.sk/models/?_m=do-get-resource-url",
                                post={'idClient': yadisk_idclient,
                                      'version' : yadisk_ver,
                                      '_model.0': 'do-get-resource-url',
                                      'sk'      : yadisk_sk,
                                      'id.0'    : yadisk_id})

        res = json_loads(result_json)
        try:
            self.link = res['models'][0]['data']['file']

        except Exception:
            self.fail(_("faild to retrieve the download url"))


getInfo = create_getInfo(YadiSk)
