import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FilerNetFolder(SimpleCrypter):
    __name__    = "FilerNetFolder"
    __type__    = "crypter"
    __version__ = "0.43"
    __status__  = "testing"

    __pattern__ = r'https?://filer\.net/folder/\w{16}'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Filer.net decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'href="(/get/\w{16})">(?!<)'

    NAME_PATTERN    = r'<h3>(?P<N>.+?) - <small'
    OFFLINE_PATTERN = r'Nicht gefunden'


getInfo = create_getInfo(FilerNetFolder)
