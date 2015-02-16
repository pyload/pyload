# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.MultiHoster import MultiHoster


class DebridItaliaCom(MultiHoster):
    __name    = "DebridItaliaCom"
    __type    = "hoster"
    __version = "0.17"

    __pattern = r'https?://(?:www\.|s\d+\.)?debriditalia\.com/dl/\d+'

    __description = """Debriditalia.com multi-hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
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
