# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class DebridItaliaCom(MultiHoster):
    __name__    = "DebridItaliaCom"
    __type__    = "hoster"
    __version__ = "0.17"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?debriditalia\.com/dl/\d+'

    __description__ = """Debriditalia.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("https://", "http://")]


    def handlePremium(self, pyfile):
        self.html = self.load("http://www.debriditalia.com/api.php",
                              get={'generate': "on", 'link': pyfile.url, 'p': self.getPassword()})

        if "ERROR:" not in self.html:
            self.link = self.html.strip()
        else:
            self.info['error'] = re.search(r'ERROR:(.*)', self.html).group(1).strip()

            self.html = self.load("http://debriditalia.com/linkgen2.php",
                                  post={'xjxfun'   : "convertiLink",
                                        'xjxargs[]': "S<![CDATA[%s]]>" % pyfile.url,
                                        'xjxargs[]': "S%s" % self.getPassword()})
            try:
                self.link = re.search(r'<a href="(.+?)"', self.html).group(1)
            except AttributeError:
                pass


getInfo = create_getInfo(DebridItaliaCom)
