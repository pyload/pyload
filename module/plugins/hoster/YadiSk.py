# -*- coding: utf-8 -*-

import re
import random

from module.common.json_layer import json_loads
from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class YadiSk(SimpleHoster):
    __name__    = "YadiSk"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "testing"

    __pattern__ = r'https?://yadi\.sk/d/[\w-]+'

    __description__ = """Yadi.sk hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", None)]


    OFFLINE_PATTERN = r'Nothing found'


    @classmethod
    def get_info(cls, url="", html=""):
        info = super(YadiSk, cls).get_info(url, html)

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
        self.resume_download = False
        self.multiDL        = False
        self.chunk_limit     = 1


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


getInfo = create_getInfo(YadiSk)
