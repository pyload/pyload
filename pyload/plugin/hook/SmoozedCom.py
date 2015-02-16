# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class SmoozedCom(MultiHook):
    __name__    = "SmoozedCom"
    __type__    = "hook"
    __version__ = "0.03"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Smoozed.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("", "")]


    def getHosters(self):
        user, data = self.account.selectAccount()
        return self.account.getAccountInfo(user)["hosters"]
