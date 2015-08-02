# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class RPNetBizHook(MultiHook):
    __name__    = "RPNetBizHook"
    __type__    = "hook"
    __version__ = "0.16"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """RPNet.biz hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Dman", "dmanugm@gmail.com")]


    def get_hosters(self):
        #: Get account data
        user, info = self.account.select()

        res = self.load("https://premium.rpnet.biz/client_api.php",
                        get={'username': user,
                             'password': info['login']['password'],
                             'action'  : "showHosterList"})
        hoster_list = json_loads(res)

        #: If account is not valid thera are no hosters available
        if 'error' in hoster_list:
            return []

        #: Extract hosters from json file
        return hoster_list['hosters']
