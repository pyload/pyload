# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import unquote

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo
from module.utils import parseFileSize


class AlldebridCom(MultiHoster):
    __name__    = "AlldebridCom"
    __type__    = "hoster"
    __version__ = "0.38"

    __pattern__ = r'https?://(?:[^/]*\.)?alldebrid\..*'

    __description__ = """Alldebrid.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Andy Voigt", "spamsales@online.de")]


    def getFilename(self, url):
        try:
            name = unquote(url.rsplit("/", 1)[1])
        except IndexError:
            name = "Unknown_Filename..."
        if name.endswith("..."):  # incomplete filename, append random stuff
            name += "%s.tmp" % randrange(100, 999)
        return name


    def setup(self):
        self.chunkLimit     = 16
        self.resumeDownload = True


    def handleMulti(self):
        password = self.getPassword()

        data = json_loads(self.load("http://www.alldebrid.com/service.php",
                                     get={'link': self.pyfile.url, 'json': "true", 'pw': password}))

        self.logDebug("Json data", data)

        if data['error']:
            if data['error'] == "This link isn't available on the hoster website.":
                self.offline()
            else:
                self.logWarning(data['error'])
                self.tempOffline()
        else:
            if self.pyfile.name and not self.pyfile.name.endswith('.tmp'):
                self.pyfile.name = data['filename']
            self.pyfile.size = parseFileSize(data['filesize'])
            self.link = data['link']

        if self.getConfig("https"):
            self.link = self.link.replace("http://", "https://")
        else:
            self.link = self.link.replace("https://", "http://")

        if self.link != self.pyfile.url:
            self.logDebug("New URL: %s" % self.link)

        if self.pyfile.name.startswith("http") or self.pyfile.name.startswith("Unknown"):
            #only use when name wasnt already set
            self.pyfile.name = self.getFilename(self.link)


        def AlldebridCom(self):
            super(AlldebridCom, self).checkFile()

            if self.checkDownload({'error': "<title>An error occured while processing your request</title>"}) is "error":
                self.retry(wait_time=60, reason=_("An error occured while generating link"))


getInfo = create_getInfo(AlldebridCom)
