#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from module.plugins.Hoster import Hoster

class BasePlugin(Hoster):
    __name__ = "BasePlugin"
    __type__ = "hoster"
    __pattern__ = r"^unmatchable$"
    __version__ = "0.1"
    __description__ = """Base Plugin when any other didnt fit"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def setup(self):
        self.chunkLimit = 3
        self.resumeDownload = True

    def process(self, pyfile):
        """main function"""

#        self.__name__ = "NetloadIn"
#        pyfile.name = "test"
#        self.load("http://localhost:9000/short")
#        self.download("http://localhost:9000/short")
#        self.decryptCaptcha("http://localhost:9000/captcha")
#        return

        if pyfile.url.startswith("http"):

            pyfile.name = re.findall("([^/=]+)", pyfile.url)[-1]
            self.download(pyfile.url)
            
        else:
            self.fail("No Plugin matched and not a downloadable url.")