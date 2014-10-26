# -*- coding: utf-8 -*-

import re

from module.common.json_layer import json_loads
from module.plugins.Hoster import Hoster


class MyfastfileCom(Hoster):
    __name__ = "MyfastfileCom"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'http://(?:www\.)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/dl/'

    __description__ = """Myfastfile.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]


    def setup(self):
        self.chunkLimit = -1
        self.resumeDownload = True


    def process(self, pyfile):
        if re.match(self.__pattern__, pyfile.url):
            new_url = pyfile.url
        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "Myfastfile.com")
            self.fail(_("No Myfastfile.com account provided"))
        else:
            self.logDebug("Original URL: %s" % pyfile.url)
            page = self.load('http://myfastfile.com/api.php',
                             get={'user': self.user, 'pass': self.account.getAccountData(self.user)['password'],
                                  'link': pyfile.url})
            self.logDebug("JSON data: " + page)
            page = json_loads(page)
            if page['status'] != 'ok':
                self.fail(_("Unable to unrestrict link"))
            new_url = page['link']

        if new_url != pyfile.url:
            self.logDebug("Unrestricted URL: " + new_url)

        self.download(new_url, disposition=True)
