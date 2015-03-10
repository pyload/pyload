# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote
from time import time

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize


class RealdebridCom(MultiHoster):
    __name__    = "RealdebridCom"
    __type__    = "hoster"
    __version__ = "0.65"

    __pattern__ = r'https?://((?:www\.|s\d+\.)?real-debrid\.com/dl/|[\w^_]\.rdb\.so/d/)[\w^_]+'

    __description__ = """Real-Debrid.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if not name or name.endswith(".."):  #: incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name


    def setup(self):
        self.chunkLimit = 3


    def handlePremium(self, pyfile):
        data = json_loads(self.load("https://real-debrid.com/ajax/unrestrict.php",
                                    get={'lang'    : "en",
                                         'link'    : pyfile.url,
                                         'password': self.getPassword(),
                                         'time'    : int(time() * 1000)}))

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

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown") or pyfile.name.endswith('..'):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(self.link)


    def checkFile(self, rules={}):
        if self.checkDownload({"error": "<title>An error occured while processing your request</title>"}):
            #usual this download can safely be retried
            self.retry(wait_time=60, reason=_("An error occured while generating link"))

        return super(RealdebridCom, self).checkFile(rules)


getInfo = create_getInfo(RealdebridCom)
