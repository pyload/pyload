# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class SmoozedComHook(MultiHook):
    __name__    = "SmoozedComHook"
    __type__    = "hook"
    __version__ = "0.03"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Smoozed.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("", "")]


    def getHosters(self):
        user, data = self.account.selectAccount()
        return self.account.getAccountInfo(user)["hosters"]
