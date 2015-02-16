# -*- coding: utf-8 -*-

import re

from random import randrange
from urllib import quote, unquote
from time import time

from pyload.utils import json_loads
from pyload.plugin.Hoster import Hoster
from pyload.utils import parseFileSize


class RealdebridCom(Hoster):
    __name__    = "RealdebridCom"
    __type__    = "hoster"
    __version__ = "0.53"

    __pattern__ = r'https?://(?:[^/]*\.)?real-debrid\..*'

    __description__ = """Real-Debrid.com hoster plugin"""
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
        self.resumeDownload = True


    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Real-debrid")
            self.fail(_("No Real-debrid account provided"))
        else:
            self.logDebug("Old URL: %s" % pyfile.url)
            password = self.getPassword().splitlines()
            if not password:
                password = ""
            else:
                password = password[0]

           data = json_loads(self.load("https://real-debrid.com/ajax/unrestrict.php",
                                        get={'lang'    : "en",
                                             'link'    : quote(pyfile.url, ""),
                                             'password': password,
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
                new_url = data['generated_links'][0][-1]

        if self.getConfig("https"):
            new_url = new_url.replace("http://", "https://")
        else:
            new_url = new_url.replace("https://", "http://")

        if new_url != pyfile.url:
            self.logDebug("New URL: %s" % new_url)

        if pyfile.name.startswith("http") or pyfile.name.startswith("Unknown") or pyfile.name.endswith('..'):
            #only use when name wasnt already set
            pyfile.name = self.getFilename(new_url)

        self.download(new_url, disposition=True)

        check = self.checkDownload(
            {"error": "<title>An error occured while processing your request</title>"})

        if check == "error":
            #usual this download can safely be retried
            self.retry(wait_time=60, reason=_("An error occured while generating link"))
