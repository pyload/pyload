# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class CrockoComFolder(SimpleCrypter):
    __name__ = "CrockoComFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?crocko.com/f/.*'

    __description__ = """Crocko.com folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    LINK_PATTERN = r'<td class="last"><a href="([^"]+)">download</a>'
