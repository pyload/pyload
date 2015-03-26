import re

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class FilerNet(SimpleCrypter):
    __name    = "FilerNet"
    __type    = "crypter"
    __version = "0.42"

    __pattern = r'https?://filer\.net/folder/\w{16}'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Filer.net decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'href="(/get/\w{16})">(?!<)'

    NAME_PATTERN    = r'<h3>(?P<N>.+?) - <small'
    OFFLINE_PATTERN = r'Nicht gefunden'
