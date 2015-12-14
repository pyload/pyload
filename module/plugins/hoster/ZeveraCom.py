# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHoster import MultiHoster


class ZeveraCom(MultiHoster):
    __name__    = "ZeveraCom"
    __type__    = "hoster"
    __version__ = "0.36"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)zevera\.com/(getFiles\.ashx|Members/download\.ashx)\?.*ourl=.+'
    __config__  = [("activated"   , "bool", "Activated"                                        , True ),
                   ("use_premium" , "bool", "Use premium account if available"                 , True ),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , False),
                   ("chk_filesize", "bool", "Check file size"                                  , True ),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10   ),
                   ("revertfailed", "bool", "Revert to standard download if fails"             , True )]

    __description__ = """Zevera.com multi-hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    FILE_ERRORS = [("Error", r'action="ErrorDownload.aspx')]


    def handle_premium(self, pyfile):
        self.link = "https://%s/getFiles.ashx?ourl=%s" % (self.account.PLUGIN_DOMAIN, pyfile.url)
