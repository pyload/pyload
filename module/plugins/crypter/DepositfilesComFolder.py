# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class DepositfilesComFolder(SimpleCrypter):
    __name__    = "DepositfilesComFolder"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?depositfiles\.com/folders/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Depositfiles.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<div class="progressName"[^>]*>\s*<a href="([^"]+)" title="[^"]*" target="_blank">'


getInfo = create_getInfo(DepositfilesComFolder)
