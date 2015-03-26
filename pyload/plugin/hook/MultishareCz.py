# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.MultiHook import MultiHook


class MultishareCz(MultiHook):
    __name    = "MultishareCz"
    __type    = "hook"
    __version = "0.07"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """MultiShare.cz hook plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="([^"]+)"></td>\s*<td class="stav">[^>]*?alt="OK"'


    def getHosters(self):
        html = self.getURL("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, html)
