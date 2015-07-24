# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class LinksnappyComHook(MultiHook):
    __name__    = "LinksnappyComHook"
    __type__    = "hook"
    __version__ = "0.05"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Linksnappy.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    def get_hosters(self):
        json_data = self.load("http://gen.linksnappy.com/lseAPI.php", get={'act': "FILEHOSTS"})
        json_data = json_loads(json_data)

        return json_data['return'].keys()
