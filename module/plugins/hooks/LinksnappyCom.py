# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class LinksnappyCom(MultiHook):
    __name__    = "LinksnappyCom"
    __type__    = "hook"
    __version__ = "0.04"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Linksnappy.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://gen.linksnappy.com/lseAPI.php", get={'act': "FILEHOSTS"})
        json_data = json_loads(json_data)

        return json_data['return'].keys()
