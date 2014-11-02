# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class BitshareComFolder(SimpleCrypter):
    __name__    = "BitshareComFolder"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?bitshare\.com/\?d=\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Bitshare.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href="(http://bitshare\.com/files/.+)">.+</a></td>'
    NAME_PATTERN = r'View public folder "(.+)"</h1>'
