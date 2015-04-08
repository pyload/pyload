# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class EasybytezComHook(MultiHook):
    __name__    = "EasybytezComHook"
    __type__    = "hook"
    __version__ = "0.07"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """EasyBytez.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def getHosters(self):
        user, data = self.account.selectAccount()

        req  = self.account.getAccountRequest(user)
        html = req.load("http://www.easybytez.com")

        return re.search(r'</textarea>\s*Supported sites:(.*)', html).group(1).split(',')
