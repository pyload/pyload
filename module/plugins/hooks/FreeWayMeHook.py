# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class FreeWayMeHook(MultiHook):
    __name__    = "FreeWayMeHook"
    __type__    = "hook"
    __version__ = "0.16"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """FreeWay.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def getHosters(self):
        user, data = self.account.selectAccount()
        hostis = self.load("http://www.free-way.bz/ajax/jd.php", get={"id": 3, "user": user, "pass": data['password']}).replace("\"", "")  #@TODO: Revert to `https` in 0.4.10
        return [x.strip() for x in hostis.split(",") if x.strip()]
