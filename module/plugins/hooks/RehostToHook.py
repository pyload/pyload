# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class RehostToHook(MultiHook):
    __name__    = "RehostToHook"
    __type__    = "hook"
    __version__ = "0.51"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Rehost.to hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org")]


    def get_hosters(self):
        user, info = self.account.select()
        html = self.load("http://rehost.to/api.php",
                           get={'cmd'     : "get_supported_och_dl",
                                'long_ses': self.account.get_data(user)['session']})
        return [x.strip() for x in html.replace("\"", "").split(",")]
