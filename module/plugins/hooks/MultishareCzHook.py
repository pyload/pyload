# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class MultishareCzHook(MultiHook):
    __name__    = "MultishareCzHook"
    __type__    = "hook"
    __version__ = "0.08"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """MultiShare.cz hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="(.+?)"></td>\s*<td class="stav">[^>]*?alt="OK"'


    def get_hosters(self):
        html = self.load("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, html)
