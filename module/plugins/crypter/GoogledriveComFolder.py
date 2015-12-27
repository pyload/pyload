# -*- coding: utf-8 -*

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class GoogledriveComFolder(SimpleCrypter):
    __name__    = "GoogledriveComFolder"
    __type__    = "crypter"
    __version__ = "0.07"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?drive\.google\.com/folderview\?.*id=\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """Drive.google.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r"folderName: '(?P<N>.+?)'"
    LINK_PATTERN    = r'\[,"\w+"(?:,,".+?")?,"(.+?)"'
    OFFLINE_PATTERN = r'<TITLE>'
