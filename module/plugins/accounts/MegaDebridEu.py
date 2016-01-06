# -*- coding: utf-8 -*-

from module.plugins.internal.MultiAccount import MultiAccount
from module.plugins.internal.misc import json


class MegaDebridEu(MultiAccount):
    __name__    = "MegaDebridEu"
    __type__    = "account"
    __version__ = "0.26"
    __status__  = "testing"

    __config__ = [("mh_mode"    , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval", "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """Mega-debrid.eu account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("D.Ducatel", "dducatel@je-geek.fr")]


    #: Define the base URL of MegaDebrid api
    API_URL = "https://www.mega-debrid.eu/api.php"


    def grab_hosters(self, user, password, data):
        reponse   = self.load("http://www.mega-debrid.eu/api.php", get={'action': "getHosters"})
        json_data = json.loads(reponse)

        if json_data['response_code'] == "ok":
            host_list = [element[0] for element in json_data['hosters']]
        else:
            self.log_error(_("Unable to retrieve hoster list"))
            host_list = []

        return host_list


    def grab_info(self, user, password, data):
        jsonResponse = self.load(self.API_URL,
                                 get={'action'  : 'connectUser',
                                      'login'   : user,
                                      'password': password})
        res = json.loads(jsonResponse)

        if res['response_code'] == "ok":
            return {'premium': True, 'validuntil': float(res['vip_end']), 'status': True}
        else:
            self.log_error(res)
            return {'status': False, 'premium': False}


    def signin(self, user, password, data):
        jsonResponse = self.load(self.API_URL,
                                 get={'action'  : 'connectUser',
                                      'login'   : user,
                                      'password': password})
        res = json.loads(jsonResponse)
        if res['response_code'] != "ok":
            self.fail_login()
