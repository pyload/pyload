# -*- coding: utf-8 -*-

from module.plugins.hooks.ZeveraComHook import ZeveraComHook


class PutdriveComHook(ZeveraComHook):
    __name__    = "PutdriveComHook"
    __type__    = "hook"
    __version__ = "0.02"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Putdrive.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]
