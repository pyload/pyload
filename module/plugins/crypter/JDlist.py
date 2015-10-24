# -*- coding: utf-8 -*-

from module.plugins.internal.Crypter import Crypter, create_getInfo


class JDlist(Crypter):
    __name__    = "JDlist"
    __type__    = "crypter"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'jdlist://(?P<LIST>[\w\+^_]+==)'
    __config__  = [("activated"         , "bool", "Activated"                          , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """JDlist decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def decrypt(self, pyfile):
        self.urls.extend(self.info['pattern']['LIST'].decode('base64').split(','))


getInfo = create_getInfo(JDlist)
