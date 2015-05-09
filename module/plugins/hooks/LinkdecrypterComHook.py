# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class LinkdecrypterComHook(MultiHook):
    __name__    = "LinkdecrypterComHook"
    __type__    = "hook"
    __version__ = "1.06"

    __config__ = [("activated"     , "bool"               , "Activated"                    , True ),
                  ("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Linkdecrypter.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def getHosters(self):
        list = re.search(r'>Supported\(\d+\)</b>: <i>(.[\w.\-, ]+)',
                         self.getURL("http://linkdecrypter.com/", decode=True).replace("(g)", "")).group(1).split(', ')
        try:
            list.remove("download.serienjunkies.org")
        except ValueError:
            pass

        return list
