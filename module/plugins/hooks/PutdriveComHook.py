# -*- coding: utf-8 -*-

from module.plugins.hooks.ZeveraComHook import ZeveraComHook


class PutdriveComHook(ZeveraComHook):
    __name__    = "PutdriveComHook"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("mode"        , "all;listed;unlisted", "Use for plugins (if supported)"               , "all"),
                  ("pluginlist"  , "str"                , "Plugin list (comma separated)"                , ""   ),
                  ("revertfailed", "bool"               , "Revert to standard download if download fails", False),
                  ("interval"    , "int"                , "Reload interval in hours (0 to disable)"      , 12   )]

    __description__ = """Putdrive.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]
