# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RehostToHook(MultiHook):
    __name__    = "RehostToHook"
    __type__    = "hook"
    __version__ = "0.50"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Rehost.to hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def getHosters(self):
        user, data = self.account.selectAccount()
        html = self.getURL("http://rehost.to/api.php",
                           get={'cmd'     : "get_supported_och_dl",
                                'long_ses': self.account.getAccountInfo(user)['session']})
        return [x.strip() for x in html.replace("\"", "").split(",")]
