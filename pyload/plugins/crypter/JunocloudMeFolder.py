# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSCrypter import XFSCrypter


class JunocloudMeFolder(XFSCrypter):
    __name__    = "JunocloudMeFolder"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?junocloud\.me/folders/(?P<ID>\d+/\w+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Junocloud.me folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "junocloud.me"
