# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class CrockoCom(SimpleCrypter):
    __name__    = "CrockoCom"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?crocko\.com/f/.*'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Crocko.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<td class="last"><a href="([^"]+)">download</a>'
