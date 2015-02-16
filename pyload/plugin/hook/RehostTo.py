# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class RehostTo(MultiHook):
    __name    = "RehostTo"
    __type    = "hook"
    __version = "0.50"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Rehost.to hook plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def getHosters(self):
        user, data = self.account.selectAccount()
        html = self.getURL("http://rehost.to/api.php",
                           get={'cmd'     : "get_supported_och_dl",
                                'long_ses': self.account.getAccountInfo(user)['session']})
        return [x.strip() for x in html.replace("\"", "").split(",")]
