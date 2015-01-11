# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RehostTo(MultiHook):
    __name__    = "RehostTo"
    __type__    = "hook"
    __version__ = "0.49"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Rehost.to hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def getHosters(self):
        user, data = self.account.selectAccount()
        page = self.getURL("http://rehost.to/api.php",
                           get={'cmd'     : "get_supported_och_dl",
                                'long_ses': self.account.getAccountData(user)['session']})
        return [x.strip() for x in page.replace("\"", "").split(",")]
