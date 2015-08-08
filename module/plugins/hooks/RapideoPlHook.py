# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class RapideoPlHook(MultiHook):
    __name__    = "RapideoPlHook"
    __type__    = "hook"
    __version__ = "0.04"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Rapideo.pl hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("goddie", "dev@rapideo.pl")]


    def get_hosters(self):
        hostings         = json_loads(self.load("https://www.rapideo.pl/clipboard.php?json=3").strip())
        hostings_domains = [domain for row in hostings for domain in row['domains'] if row['sdownload'] == "0"]

        self.log_debug(hostings_domains)

        return hostings_domains
