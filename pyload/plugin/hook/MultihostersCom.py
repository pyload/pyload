# -*- coding: utf-8 -*-

from pyload.plugin.hook.ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name    = "MultihostersCom"
    __type    = "hook"
    __version = "0.02"

    __config = [("mode"        , "all;listed;unlisted", "Use for plugins (if supported)"               , "all"),
                  ("pluginlist"  , "str"                , "Plugin list (comma separated)"                , ""   ),
                  ("revertfailed", "bool"               , "Revert to standard download if download fails", False),
                  ("interval"    , "int"                , "Reload interval in hours (0 to disable)"      , 12   )]

    __description = """Multihosters.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("tjeh", "tjeh@gmx.net")]
