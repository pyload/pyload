# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class PremiumTo(MultiHook):
    __name__    = "PremiumTo"
    __type__    = "hook"
    __version__ = "0.08"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Premium.to hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        page = self.getURL("http://premium.to/api/hosters.php",
                      get={'username': self.account.username, 'password': self.account.password})
        return [x.strip() for x in page.replace("\"", "").split(";")]
