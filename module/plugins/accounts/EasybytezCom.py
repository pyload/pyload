# -*- coding: utf-8 -*-

import re

from module.plugins.internal.XFSAccount import XFSAccount


class EasybytezCom(XFSAccount):
    __name__    = "EasybytezCom"
    __type__    = "account"
    __version__ = "0.16"
    __status__  = "testing"

    __config__ = [("mh_activated", "bool"               , "Use multihoster feature"      , True ),
                  ("mh_mode"     , "all;listed;unlisted", "Filter hosters to use"        , "all"),
                  ("mh_list"     , "str"                , "Hoster list (comma separated)", ""   ),
                  ("mh_interval" , "int"                , "Reload interval in minutes"   , 60   )]

    __description__ = """EasyBytez.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    PLUGIN_DOMAIN = "easybytez.com"


    def grab_hosters(self, user, password, data):
        return re.search(r'</textarea>\s*Supported sites:(.*)',
                         self.load("http://www.easybytez.com")).group(1).split(',')
