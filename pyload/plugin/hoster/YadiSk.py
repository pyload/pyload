# -*- coding: utf-8 -*-

import random
import re

from pyload.plugin.internal.SimpleHoster import SimpleHoster
from pyload.utils import json_loads


class YadiSk(SimpleHoster):
    __name    = "YadiSk"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'https?://yadi\.sk/d/[\w-]+'

    __description = """Yadi.sk hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("GammaC0de", None)]


    OFFLINE_PATTERN = r'Nothing found'


    @classmethod
    def getInfo(cls, url="", html=""):
        info = super(YadiSk, cls).getInfo(url, html)

        if html:
            if 'idclient' not in info:
                info['idclient'] = ""
                for _i in xrange(32):
                    info ['idclient']  += random.choice('0123456abcdef')

            m = re.search(r'<script id="models-client" type="application/json">(.+?)</script>', html)
            if m:
                api_data = json_loads(m.group(1))
                try:
                    for sect in api_data:
                        if 'model' in sect:
                            if sect['model'] == "config":
                                info['version'] = sect['data']['version']
                                info['sk']  = sect['data']['sk']

                            elif sect['model'] == "resource":
                                info['id']   = sect['data']['id']
                                info['size'] = sect['data']['meta']['size']
                                info['name'] = sect['data']['name']

                except Exception, e:
                    info['status'] = 8
                    info['error'] = _("Unexpected server response: %s") % e.message

            else:
                info['status'] = 8
                info['error'] = _("could not find required json data")

        return info


    def setup(self):
        self.resumeDownload = False
        self.multiDL        = False
        self.chunkLimit     = 1


    def handle_free(self, pyfile):
        if any(True for _k in ['id', 'sk', 'version', 'idclient'] if _k not in self.info):
           self.error(_("Missing JSON data"))


        try:
            self.html = self.load("https://yadi.sk/models/",
                                  get={'_m': "do-get-resource-url"},
                                  post={'idClient': self.info['idclient'],
                                        'version' : self.info['version'],
                                        '_model.0': "do-get-resource-url",
                                        'sk'      : self.info['sk'],
                                        'id.0'    : self.info['id']})

            self.link = json_loads(self.html)['models'][0]['data']['file']

        except Exception:
            pass
