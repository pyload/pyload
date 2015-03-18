# -*- coding: utf-8 -*-

import re
import time

from random import randrange
from urllib import unquote

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize


class RealdebridCom(MultiHoster):
    __name__    = "RealdebridCom"
    __type__    = "hoster"
    __version__ = "0.67"

    __pattern__ = r'https?://((?:www\.|s\d+\.)?real-debrid\.com/dl/|[\w^_]\.rdb\.so/d/)[\w^_]+'

    __description__ = """Real-Debrid.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def setup(self):
        self.chunkLimit = 3


    def handlePremium(self, pyfile):
        data = json_loads(self.load("https://real-debrid.com/ajax/unrestrict.php",
                                    get={'lang'    : "en",
                                         'link'    : pyfile.url,
                                         'password': self.getPassword(),
                                         'time'    : int(time.time() * 1000)}))

        self.logDebug("Returned Data: %s" % data)

        if data['error'] != 0:
            if data['message'] == "Your file is unavailable on the hoster.":
                self.offline()
            else:
                self.logWarning(data['message'])
                self.tempOffline()
        else:
            if pyfile.name is not None and pyfile.name.endswith('.tmp') and data['file_name']:
                pyfile.name = data['file_name']
            pyfile.size = parseFileSize(data['file_size'])
            self.link = data['generated_links'][0][-1]

        if self.getConfig('ssl'):
            self.link = self.link.replace("http://", "https://")
        else:
            self.link = self.link.replace("https://", "http://")


getInfo = create_getInfo(RealdebridCom)
