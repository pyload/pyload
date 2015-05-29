# -*- coding: utf-8 -*-

from module.plugins.internal.MultiHook import MultiHook


class FreeWayMeHook(MultiHook):
    __name__    = "FreeWayMeHook"
    __type__    = "hook"
    __version__ = "0.15"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description__ = """FreeWay.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def getHosters(self):
        # Get account data
        if not self.account or not self.account.canUse():
           hostis = self.getURL("https://www.free-way.me/ajax/jd.php", get={"id": 3}).replace("\"", "").strip()
        else:
           self.logDebug("AccountInfo available - Get HosterList with User Pass")
           (user, data) = self.account.selectAccount()
           hostis = self.getURL("https://www.free-way.me/ajax/jd.php", get={"id": 3, "user": user, "pass": data['password']}).replace("\"", "").strip()

        self.logDebug("hosters: %s" % hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
