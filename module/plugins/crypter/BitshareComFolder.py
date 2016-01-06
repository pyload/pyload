# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class BitshareComFolder(SimpleCrypter):
    __name__    = "BitshareComFolder"
    __type__    = "crypter"
    __version__ = "0.09"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/\?d=\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """Bitshare.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href="(http://bitshare\.com/files/.+)">.+</a></td>'
    NAME_PATTERN = r'View public folder "(?P<N>.+?)"</h1>'
