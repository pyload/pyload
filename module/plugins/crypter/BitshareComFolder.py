# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class BitshareComFolder(SimpleCrypter):
    __name__    = "BitshareComFolder"
    __type__    = "crypter"
    __version__ = "0.05"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/\?d=\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Bitshare.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href="(http://bitshare\.com/files/.+)">.+</a></td>'
    NAME_PATTERN = r'View public folder "(?P<N>.+?)"</h1>'


getInfo = create_getInfo(BitshareComFolder)
