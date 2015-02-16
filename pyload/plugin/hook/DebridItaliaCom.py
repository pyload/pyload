# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.MultiHook import MultiHook


class DebridItaliaCom(MultiHook):
    __name    = "DebridItaliaCom"
    __type    = "hook"
    __version = "0.12"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Debriditalia.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHosters(self):
        return self.getURL("http://debriditalia.com/api.php", get={'hosts': ""}).replace('"', '').split(',')
