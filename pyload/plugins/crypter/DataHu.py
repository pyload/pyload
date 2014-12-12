# -*- coding: utf-8 -*-

import re

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class DataHu(SimpleCrypter):
    __name    = "DataHu"
    __type    = "crypter"
    __version = "0.06"

    __pattern = r'http://(?:www\.)?data\.hu/dir/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Data.hu folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("crash", ""),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href=\'(http://data\.hu/get/.+)\' target=\'_blank\'>\1</a>'
    NAME_PATTERN = ur'<title>(?P<N>.+) Let\xf6lt\xe9se</title>'


    def prepare(self):
        super(DataHu, self).prepare()

        if u'K\xe9rlek add meg a jelsz\xf3t' in self.html:  # Password protected
            password = self.getPassword()
            if not password:
                self.fail(_("Password required"))

            self.logDebug("The folder is password protected', 'Using password: " + password)

            self.html = self.load(self.pyfile.url, post={'mappa_pass': password}, decode=True)

            if u'Hib\xe1s jelsz\xf3' in self.html:  # Wrong password
                self.fail(_("Wrong password"))
