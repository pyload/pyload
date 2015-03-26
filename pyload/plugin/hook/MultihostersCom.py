# -*- coding: utf-8 -*-

from pyload.plugin.hook.ZeveraCom import ZeveraCom


class MultihostersCom(ZeveraCom):
    __name__    = "MultihostersCom"
    __type__    = "hook"
    __version__ = "0.02"

    __config__ = [("mode"        , "all;listed;unlisted", "Use for plugins (if supported)"               , "all"),
                  ("pluginlist"  , "str"                , "Plugin list (comma separated)"                , ""   ),
                  ("revertfailed", "bool"               , "Revert to standard download if download fails", False),
                  ("interval"    , "int"                , "Reload interval in hours (0 to disable)"      , 12   )]

    __description__ = """Multihosters.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("tjeh", "tjeh@gmx.net")]
