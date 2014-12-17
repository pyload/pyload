# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class DebridItaliaCom(SimpleHoster):
    __name__    = "DebridItaliaCom"
    __type__    = "hoster"
    __version__ = "0.08"

    __pattern__ = r'http://s\d+\.debriditalia\.com/dl/\d+'

    __description__ = """Debriditalia.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.chunkLimit     = -1
        self.resumeDownload = True


    def handleMulti(self):
        html = self.load("http://www.debriditalia.com/api.php",
                         get={'generate': "on", 'link': self.pyfile.url, 'p': self.getPassword()})

        if "ERROR" in html:
            self.fail(re.search(r'ERROR:(.*)', html).strip())

        self.link = html.strip()


    def checkFile(self):
        check = self.checkDownload({'empty': re.compile(r'^$')})
        if check == "empty":
            self.retry(5, 2 * 60, "Empty file downloaded")


getInfo = create_getInfo(DebridItaliaCom)
