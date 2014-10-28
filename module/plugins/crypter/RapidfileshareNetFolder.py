# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPCrypter import XFSPCrypter


class RapidfileshareNetFolder(XFSPCrypter):
    __name__    = "RapidfileshareNetFolder"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?rapidfileshare\.net/users/\w+/\d+/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Rapidfileshare.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_NAME = "rapidfileshare.net"
