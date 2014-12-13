# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class CrockoCom(SimpleCrypter):
    __name    = "CrockoCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?crocko\.com/f/.*'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Crocko.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<td class="last"><a href="([^"]+)">download</a>'
