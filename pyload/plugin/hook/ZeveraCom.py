# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class ZeveraCom(MultiHook):
    __name    = "ZeveraCom"
    __type    = "hook"
    __version = "0.05"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("retry"         , "int"                , "Number of retries before revert"     , 10   ),
                  ("retryinterval" , "int"                , "Retry interval in minutes"           , 1    ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """Zevera.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHosters(self):
        html = self.account.api_response(pyreq.getHTTPRequest(timeout=120), cmd="gethosters")
        return [x.strip() for x in html.split(",")]
