# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class LinkdecrypterCom(MultiHook):
    __name__    = "LinkdecrypterCom"
    __type__    = "hook"
    __version__ = "1.00"

    __config__ = [("mode"        , "all;listed;unlisted", "Use for crypters (if supported)"              , "all"),
                  ("pluginlist"  , "str"                , "Crypter list (comma separated)"               , ""   ),
                  ("interval"    , "int"                , "Reload interval in hours (0 to disable)"      , 12   )]

    __description__ = """Linkdecrypter.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def getCrypters(self):
        try:
            html = self.getURL("http://linkdecrypter.com/")
            return re.search(r'>Supported\(\d+\)</b>: <i>(.+?) \+ RSDF', html).group(1).split(', ')
        except Exception:
            return list()
