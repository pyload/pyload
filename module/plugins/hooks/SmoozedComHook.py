# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class SmoozedComHook(MultiHook):
    __name__    = "SmoozedComHook"
    __type__    = "hook"
    __version__ = "0.04"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Smoozed.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("", "")]


    def get_hosters(self):
        user, info = self.account.select()
        return self.account.get_data(user)['hosters']
