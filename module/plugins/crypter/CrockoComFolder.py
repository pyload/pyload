# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class CrockoComFolder(SimpleCrypter):
    __name__ = "CrockoComFolder"
    __version__ = "0.01"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?crocko.com/f/.*'

    __description__ = """Crocko.com folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    LINK_PATTERN = r'<td class="last"><a href="([^"]+)">download</a>'
