# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster, create_getInfo, replace_patterns


class SimplydebridCom(MultiHoster):
    __name__    = "SimplydebridCom"
    __type__    = "hoster"
    __version__ = "0.20"
    __status__  = "testing"

    __pattern__ = r'http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/sd\.php'
    __config__  = [("use_premium" , "bool", "Use premium account if available"    , True),
                   ("revertfailed", "bool", "Revert to standard download if fails", True)]

    __description__ = """Simply-debrid.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def handle_premium(self, pyfile):
        #: Fix the links for simply-debrid.com!
        self.link = replace_patterns(pyfile.url, [("clz.to", "cloudzer.net/file")
                                                  ("http://share-online", "http://www.share-online")
                                                  ("ul.to", "uploaded.net/file")
                                                  ("uploaded.com", "uploaded.net")
                                                  ("filerio.com", "filerio.in")
                                                  ("lumfile.com", "lumfile.se")])

        if 'fileparadox' in self.link:
            self.link = self.link.replace("http://", "https://")

        self.html = self.load("http://simply-debrid.com/api.php", get={'dl': self.link})
        if 'tiger Link' in self.html or 'Invalid Link' in self.html or ('API' in self.html and 'ERROR' in self.html):
            self.error(_("Unable to unrestrict link"))

        self.link = self.html

        self.wait(5)


    def check_file(self):
        if self.check_download({'error': "No address associated with hostname"}):
            self.retry(24, 3 * 60, _("Bad file downloaded"))

        return super(SimplydebridCom, self).check_file()


getInfo = create_getInfo(SimplydebridCom)
