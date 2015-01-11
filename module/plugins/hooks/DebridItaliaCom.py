# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class DebridItaliaCom(MultiHook):
    __name__    = "DebridItaliaCom"
    __type__    = "hook"
    __version__ = "0.12"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Debriditalia.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHosters(self):
        return self.getURL("http://debriditalia.com/api.php", get={'hosts': ""}).replace('"', '').split(',')
