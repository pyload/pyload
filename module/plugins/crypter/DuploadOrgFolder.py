# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class DuploadOrgFolder(DeadCrypter):
    __name__    = "DuploadOrgFolder"
    __type__    = "crypter"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?dupload\.org/folder/\d+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Dupload.org folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


getInfo = create_getInfo(DuploadOrgFolder)
