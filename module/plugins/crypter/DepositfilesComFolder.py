# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DepositfilesComFolder(SimpleCrypter):
    __name__ = "DepositfilesComFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?depositfiles.com/folders/\w+'

    __description__ = """Depositfiles.com folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    LINK_PATTERN = r'<div class="progressName"[^>]*>\s*<a href="([^"]+)" title="[^"]*" target="_blank">'
