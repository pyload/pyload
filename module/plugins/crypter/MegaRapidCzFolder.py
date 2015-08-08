# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class MegaRapidCzFolder(SimpleCrypter):
    __name__    = "MegaRapidCzFolder"
    __type__    = "crypter"
    __version__ = "0.03"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?(share|mega)rapid\.cz/slozka/\d+/\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Share-Rapid.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<td class="soubor".*?><a href="(.+?)">'


getInfo = create_getInfo(MegaRapidCzFolder)
