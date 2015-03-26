# -*- coding: utf-8 -*-

import re

from pyload.plugin.internal.MultiHook import MultiHook


class EasybytezCom(MultiHook):
    __name    = "EasybytezCom"
    __type    = "hook"
    __version = "0.07"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """EasyBytez.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def getHosters(self):
        user, data = self.account.selectAccount()

        req  = self.account.getAccountRequest(user)
        html = req.load("http://www.easybytez.com")

        return re.search(r'</textarea>\s*Supported sites:(.*)', html).group(1).split(',')
