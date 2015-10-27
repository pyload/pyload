# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class DataHuFolder(SimpleCrypter):
    __name__    = "DataHuFolder"
    __type__    = "crypter"
    __version__ = "0.11"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?data\.hu/dir/\w+'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Data.hu folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("crash", None),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href=\'(http://data\.hu/get/.+)\' target=\'_blank\'>\1</a>'
    NAME_PATTERN = ur'<title>(?P<N>.+?) Let\xf6lt\xe9se</title>'


    def prepare(self):
        super(DataHuFolder, self).prepare()

        if u'K\xe9rlek add meg a jelsz\xf3t' in self.data:  #: Password protected
            password = self.get_password()
            if not password:
                self.fail(_("Password required"))

            self.log_debug("The folder is password protected', 'Using password: " + password)

            self.data = self.load(self.pyfile.url, post={'mappa_pass': password})

            if u'Hib\xe1s jelsz\xf3' in self.data:  #: Wrong password
                self.fail(_("Wrong password"))


getInfo = create_getInfo(DataHuFolder)
