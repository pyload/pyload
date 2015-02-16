# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.MultiHook import MultiHook


class LinkdecrypterCom(MultiHook):
    __name    = "LinkdecrypterCom"
    __type    = "hook"
    __version = "1.02"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Linkdecrypter.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def getCrypters(self):
        return re.search(r'>Supported\(\d+\)</b>: <i>(.[\w.\-, ]+)',
                         self.getURL("http://linkdecrypter.com/").replace("(g)", "")).group(1).split(', ')
