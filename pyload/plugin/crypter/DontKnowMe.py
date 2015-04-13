# -*- coding: utf-8 -*-

from pyload.plugin.Crypter import Crypter


class DontKnowMe(SimpleDereferer):
    __name    = "DontKnowMe"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?dontknow\.me/at/\?(?P<LINK>.+)'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """DontKnow.me decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("selaux", "")]
