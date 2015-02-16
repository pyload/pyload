# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSCrypter import XFSCrypter


class RapidfileshareNet(XFSCrypter):
    __name__    = "RapidfileshareNet"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?rapidfileshare\.net/users/\w+/\d+/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Rapidfileshare.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "rapidfileshare.net"
