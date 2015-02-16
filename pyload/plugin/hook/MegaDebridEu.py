# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class MegaDebridEu(MultiHook):
    __name    = "MegaDebridEu"
    __type    = "hook"
    __version = "0.05"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Mega-debrid.eu hook plugin"""
    __license     = "GPLv3"
    __authors     = [("D.Ducatel", "dducatel@je-geek.fr")]


    def getHosters(self):
        reponse   = self.getURL("http://www.mega-debrid.eu/api.php", get={'action': "getHosters"})
        json_data = json_loads(reponse)

        if json_data['response_code'] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.logError(_("Unable to retrieve hoster list"))
            host_list = list()

        return host_list
