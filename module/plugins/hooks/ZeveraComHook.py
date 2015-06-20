# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class ZeveraComHook(MultiHook):
    __name__    = "ZeveraComHook"
    __type__    = "hook"
    __version__ = "0.05"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """Zevera.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg"      , "zoidberg@mujmail.cz"),
                       ("Walter Purcaro", "vuolter@gmail.com"  )]


    def getHosters(self):
        html = self.account.api_response(pyreq.getHTTPRequest(timeout=120), cmd="gethosters")
        return [x.strip() for x in html.split(",")]
