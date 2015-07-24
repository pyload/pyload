# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class MegaDebridEuHook(MultiHook):
    __name__    = "MegaDebridEuHook"
    __type__    = "hook"
    __version__ = "0.06"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Mega-debrid.eu hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    def get_hosters(self):
        reponse   = self.load("http://www.mega-debrid.eu/api.php", get={'action': "getHosters"})
        json_data = json_loads(reponse)

        if json_data['response_code'] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.log_error(_("Unable to retrieve hoster list"))
            host_list = []

        return host_list
