# -*- coding: utf-8 -*-

from module.plugins.hooks.ZeveraComHook import ZeveraComHook


class MultihostersComHook(ZeveraComHook):
    __name__    = "MultihostersComHook"
    __type__    = "hook"
    __version__ = "0.03"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Multihosters.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("tjeh", "tjeh@gmx.net")]
