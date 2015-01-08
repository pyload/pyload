# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class LinkdecrypterCom(MultiHook):
    __name__    = "LinkdecrypterCom"
    __type__    = "hook"
    __version__ = "1.01"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Linkdecrypter.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def getCrypters(self):
        try:
            html = self.getURL("http://linkdecrypter.com/")
            return re.search(r'>Supported\(\d+\)</b>: <i>(.+?) \+ RSDF', html).group(1).split(', ')
        except Exception:
            return list()
