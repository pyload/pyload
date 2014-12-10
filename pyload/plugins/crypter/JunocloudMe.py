# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFSCrypter import XFSCrypter


class JunocloudMe(XFSCrypter):
    __name    = "JunocloudMe"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?junocloud\.me/folders/(?P<ID>\d+/\w+)'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Junocloud.me folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_DOMAIN = "junocloud.me"
