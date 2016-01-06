# -*- coding: utf-8 -*-

from module.plugins.internal.Account import Account


class MultiAccount(Account):
    __name__    = "MultiAccount"
    __type__    = "account"
    __version__ = "0.05"
    __status__  = "broken"

    __config__ = [("activated"     , "bool"               , "Activated"                    , True ),
                  ("multi"         , "bool"               , "Multi-hoster"                 , True ),
                  ("multi_mode"    , "all;listed;unlisted", "Hosters to use"               , "all"),
                  ("multi_list"    , "str"                , "Hoster list (comma separated)", ""   ),
                  ("multi_interval", "int"                , "Reload interval in hours"     , 12   )]

    __description__ = """Multi-hoster account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]
