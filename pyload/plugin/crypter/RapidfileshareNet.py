# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSCrypter import XFSCrypter


class RapidfileshareNet(XFSCrypter):
    __name    = "RapidfileshareNet"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?rapidfileshare\.net/users/\w+/\d+/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Rapidfileshare.net folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "rapidfileshare.net"
