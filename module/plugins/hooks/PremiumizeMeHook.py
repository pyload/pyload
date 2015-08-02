# -*- coding: utf-8 -*-

from module.common.json_layer import json_loads
from module.plugins.internal.MultiHook import MultiHook


class PremiumizeMeHook(MultiHook):
    __name__    = "PremiumizeMeHook"
    __type__    = "hook"
    __version__ = "0.20"
    __status__  = "testing"

    __config__ = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"              , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)", ""   ),
                  ("reload"        , "bool"               , "Reload plugin list"           , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Premiumize.me hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Florian Franzen", "FlorianFranzen@gmail.com")]


    def get_hosters(self):
        #: Get account data
        user, info = self.account.select()

        #: Get supported hosters list from premiumize.me using the
        #: json API v1 (see https://secure.premiumize.me/?show=api)
        answer = self.load("http://api.premiumize.me/pm-api/v1.php",  #@TODO: Revert to `https` in 0.4.10
                           get={'method'       : "hosterlist",
                                'params[login]': user,
                                'params[pass]' : info['login']['password']})
        data = json_loads(answer)

        #: If account is not valid thera are no hosters available
        if data['status'] != 200:
            return []

        #: Extract hosters from json file
        return data['result']['hosterlist']
