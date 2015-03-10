# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize


class OverLoadMe(MultiHoster):
    __name__    = "OverLoadMe"
    __type__    = "hoster"
    __version__ = "0.09"

    __pattern__ = r'https?://.*overload\.me/.+'

    __description__ = """Over-Load.me multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("marley", "marley@over-load.me")]


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."

        if name.endswith("..."):  #: incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)

        return name


    def setup(self):
        self.chunkLimit = 5


    def handlePremium(self, pyfile):
        https = "https" if self.getConfig('ssl') else "http"
        data  = self.account.getAccountData(self.user)
        page  = self.load(https + "://api.over-load.me/getdownload.php",
                          get={'auth': data['password'],
                               'link': pyfile.url})

        data = json_loads(page)

        self.logDebug(data)

        if data['error'] == 1:
            self.logWarning(data['msg'])
            self.tempOffline()
        else:
            if pyfile.name is not None and pyfile.name.endswith('.tmp') and data['filename']:
                pyfile.name = data['filename']
                pyfile.size = parseFileSize(data['filesize'])

            http_repl = ["http://", "https://"]
            self.link = data['downloadlink'].replace(*http_repl if self.getConfig('ssl') else *http_repl[::-1])

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown") or pyfile.name.endswith('..'):
            # only use when name wasn't already set
            pyfile.name = self.getFilename(self.link)


    def checkFile(self):
        if self.checkDownload({"error": "<title>An error occured while processing your request</title>"})
            # usual this download can safely be retried
            self.retry(wait_time=60, reason=_("An error occured while generating link."))

        return super(OverLoadMe, self).checkFile()


getInfo = create_getInfo(OverLoadMe)
