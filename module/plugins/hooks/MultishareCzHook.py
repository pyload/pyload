# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class MultishareCzHook(MultiHook):
    __name__    = "MultishareCzHook"
    __type__    = "hook"
    __version__ = "0.07"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """MultiShare.cz hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="(.+?)"></td>\s*<td class="stav">[^>]*?alt="OK"'


    def getHosters(self):
        html = self.getURL("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, html)
