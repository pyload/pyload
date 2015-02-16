# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.plugin.internal.MultiHook import MultiHook


class RPNetBiz(MultiHook):
    __name    = "RPNetBiz"
    __type    = "hook"
    __version = "0.14"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """RPNet.biz hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Dman", "dmanugm@gmail.com")]


    def getHosters(self):
        # Get account data
        user, data = self.account.selectAccount()

        res = self.getURL("https://premium.rpnet.biz/client_api.php",
                     get={'username': user, 'password': data['password'], 'action': "showHosterList"})
        hoster_list = json_loads(res)

        # If account is not valid thera are no hosters available
        if 'error' in hoster_list:
            return []

        # Extract hosters from json file
        return hoster_list['hosters']
