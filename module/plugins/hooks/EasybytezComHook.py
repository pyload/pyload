# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class EasybytezComHook(MultiHook):
    __name__    = "EasybytezComHook"
    __type__    = "hook"
    __version__ = "0.08"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """EasyBytez.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def get_hosters(self):
        user, info = self.account.select()

        html = self.load("http://www.easybytez.com",
                         req=self.account.get_request(user))

        return re.search(r'</textarea>\s*Supported sites:(.*)', html).group(1).split(',')
