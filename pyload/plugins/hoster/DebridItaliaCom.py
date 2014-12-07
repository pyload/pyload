# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.Hoster import Hoster
from pyload.plugins.internal.SimpleHoster import replace_patterns


class DebridItaliaCom(Hoster):
    __name__    = "DebridItaliaCom"
    __type__    = "hoster"
    __version__ = "0.07"

    __pattern__ = r'http://s\d+\.debriditalia\.com/dl/\d+'

    __description__ = """Debriditalia.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS  = [(r'(/dl/\d+)$', '\1/')]


    def setup(self):
        self.chunkLimit     = -1
        self.resumeDownload = True


    def process(self, pyfile):
        pyfile.url = replace_patterns(pyfile.url, cls.URL_REPLACEMENTS)

        if re.match(self.__pattern__, pyfile.url):
            link = pyfile.url

        elif not self.account:
            self.logError(_("Please enter your %s account or deactivate this plugin") % "DebridItalia")
            self.fail(_("No DebridItalia account provided"))

        else:
            html = self.load("http://www.debriditalia.com/api.php", get={'generate': "", 'link': pyfile.url})

            if "ERROR" in html:
                self.fail(re.search(r'ERROR:(.*)', html).strip())

            link = html.strip()

        self.download(link, disposition=True)

        check = self.checkDownload({'empty': re.compile(r'^$')})

        if check == "empty":
            self.retry(5, 2 * 60, "Empty file downloaded")
