# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class LinkSaveIn(SimpleCrypter):
    __name__    = "LinkSaveIn"
    __type__    = "crypter"
    __version__ = "2.06"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?linksave\.in/\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """LinkSave.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("linksave.in", "Linksave_Language", "english")]

    OFFLINE_PATTERN = r'>(Error )?404 -'


getInfo = create_getInfo(LinkSaveIn)
