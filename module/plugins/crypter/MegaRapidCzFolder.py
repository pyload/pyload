# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class MegaRapidCzFolder(SimpleCrypter):
    __name__ = "MegaRapidCzFolder"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?(share|mega)rapid\.cz/slozka/\d+/\w+'

    __description__ = """Share-Rapid.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<td class="soubor"[^>]*><a href="([^"]+)">'
