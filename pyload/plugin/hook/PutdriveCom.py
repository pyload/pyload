# -*- coding: utf-8 -*-

from pyload.plugin.hook.ZeveraCom import ZeveraCom


class PutdriveCom(ZeveraCom):
    __name    = "PutdriveCom"
    __type    = "hook"
    __version = "0.01"

    __config = [("mode"        , "all;listed;unlisted", "Use for plugins (if supported)"               , "all"),
                  ("pluginlist"  , "str"                , "Plugin list (comma separated)"                , ""   ),
                  ("revertfailed", "bool"               , "Revert to standard download if download fails", False),
                  ("interval"    , "int"                , "Reload interval in hours (0 to disable)"      , 12   )]

    __description = """Putdrive.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]
