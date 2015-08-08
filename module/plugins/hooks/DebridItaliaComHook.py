# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class DebridItaliaComHook(MultiHook):
    __name__    = "DebridItaliaComHook"
    __type__    = "hook"
    __version__ = "0.13"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Debriditalia.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell"      , "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com"  )]


    def get_hosters(self):
        return self.load("http://debriditalia.com/api.php", get={'hosts': ""}).replace('"', '').split(',')
