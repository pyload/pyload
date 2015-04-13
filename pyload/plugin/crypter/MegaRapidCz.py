# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class MegaRapidCz(SimpleCrypter):
    __name    = "MegaRapidCz"
    __type    = "crypter"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?(share|mega)rapid\.cz/slozka/\d+/\w+'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Share-Rapid.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<td class="soubor".*?><a href="(.+?)">'
