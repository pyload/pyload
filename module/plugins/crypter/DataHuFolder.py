# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DataHuFolder(SimpleCrypter):
    __name__    = "DataHuFolder"
    __type__    = "crypter"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?data\.hu/dir/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Data.hu folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("crash", None),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href=\'(http://data\.hu/get/.+)\' target=\'_blank\'>\1</a>'
    NAME_PATTERN = ur'<title>(?P<N>.+) Let\xf6lt\xe9se</title>'


    def prepare(self):
        super(DataHuFolder, self).prepare()

        if u'K\xe9rlek add meg a jelsz\xf3t' in self.html:  # Password protected
            password = self.getPassword()
            if not password:
                self.fail(_("Password required"))

            self.logDebug("The folder is password protected', 'Using password: " + password)

            self.html = self.load(self.pyfile.url, post={'mappa_pass': password}, decode=True)

            if u'Hib\xe1s jelsz\xf3' in self.html:  # Wrong password
                self.fail(_("Wrong password"))
