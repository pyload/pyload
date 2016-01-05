# -*- coding: utf-8 -*-
#
# Test links:
# http://fileom.com/gycaytyzdw3g/random.bin.html

from module.plugins.internal.XFSHoster import XFSHoster


class FileomCom(XFSHoster):
    __name__    = "FileomCom"
    __type__    = "hoster"
    __version__ = "0.10"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?fileom\.com/\w{12}'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Fileom.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PLUGIN_DOMAIN = "fileom.com"

    NAME_PATTERN = r'Filename: <span>(?P<N>.+?)<'
    SIZE_PATTERN = r'File Size: <span class="size">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    LINK_PATTERN = r'var url2 = \'(.+?)\';'


    def setup(self):
        self.multiDL = True
        self.chunk_limit = 1
        self.resume_download = self.premium
