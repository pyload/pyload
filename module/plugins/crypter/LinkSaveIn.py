# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class LinkSaveIn(SimpleCrypter):
    __name__    = "LinkSaveIn"
    __type__    = "crypter"
    __version__ = "2.08"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?linksave\.in/\w+'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """LinkSave.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    COOKIES = [("linksave.in", "Linksave_Language", "english")]

    OFFLINE_PATTERN = r'>(Error )?404 -'


getInfo = create_getInfo(LinkSaveIn)
