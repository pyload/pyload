# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class PremiumTo(MultiHook):
    __name    = "PremiumTo"
    __type    = "hook"
    __version = "0.08"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Premium.to hook plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("zoidberg", "zoidberg@mujmail.cz"),
                       ("stickell", "l.stickell@yahoo.it")]


    def getHosters(self):
        html = self.getURL("http://premium.to/api/hosters.php",
                      get={'username': self.account.username, 'password': self.account.password})
        return [x.strip() for x in html.replace("\"", "").split(";")]
