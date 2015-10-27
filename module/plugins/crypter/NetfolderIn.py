# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class NetfolderIn(DeadCrypter):
    __name__    = "NetfolderIn"
    __type__    = "crypter"
    __version__ = "0.76"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?netfolder\.(in|me)/(folder\.php\?folder_id=)?(?P<ID>\w+)(?(1)|/\w+)'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """NetFolder.in decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("fragonib", "fragonib[AT]yahoo[DOT]es")]


getInfo = create_getInfo(NetfolderIn)
