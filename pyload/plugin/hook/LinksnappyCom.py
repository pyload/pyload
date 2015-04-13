# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class LinksnappyCom(MultiHook):
    __name    = "LinksnappyCom"
    __type    = "hook"
    __version = "0.04"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Linksnappy.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        json_data = self.getURL("http://gen.linksnappy.com/lseAPI.php", get={'act': "FILEHOSTS"})
        json_data = json_loads(json_data)

        return json_data['return'].keys()
