# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo


class DebridItaliaCom(MultiHoster):
    __name__    = "DebridItaliaCom"
    __type__    = "hoster"
    __version__ = "0.21"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.|s\d+\.)?debriditalia\.com/dl/\d+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Debriditalia.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    URL_REPLACEMENTS = [("https://", "http://")]


    def handle_premium(self, pyfile):
        self.data = self.load("http://www.debriditalia.com/api.php",
                              get={'generate': "on", 'link': pyfile.url, 'p': self.get_password()})

        if "ERROR:" not in self.data:
            self.link = self.data
        else:
            self.info['error'] = re.search(r'ERROR:(.*)', self.data).group(1).strip()

            self.data = self.load("http://debriditalia.com/linkgen2.php",
                                  post={'xjxfun'   : "convertiLink",
                                        'xjxargs[]': "S<![CDATA[%s]]>" % pyfile.url,
                                        'xjxargs[]': "S%s" % self.get_password()})
            try:
                self.link = re.search(r'<a href="(.+?)"', self.data).group(1)
            except AttributeError:
                pass


getInfo = create_getInfo(DebridItaliaCom)
