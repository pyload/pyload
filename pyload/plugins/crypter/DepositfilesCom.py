# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class DepositfilesCom(SimpleCrypter):
    __name    = "DepositfilesCom"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?depositfiles\.com/folders/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Depositfiles.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<div class="progressName"[^>]*>\s*<a href="([^"]+)" title="[^"]*" target="_blank">'
