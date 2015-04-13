# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class BitshareCom(SimpleCrypter):
    __name    = "BitshareCom"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?bitshare\.com/\?d=\w+'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Bitshare.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href="(http://bitshare\.com/files/.+)">.+</a></td>'
    NAME_PATTERN = r'View public folder "(?P<N>.+)"</h1>'
