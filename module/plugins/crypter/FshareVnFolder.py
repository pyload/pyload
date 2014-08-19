# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FshareVnFolder(SimpleCrypter):
    __name__ = "FshareVnFolder"
    __version__ = "0.01"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?fshare.vn/folder/.*'

    __description__ = """Fshare.vn folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    LINK_PATTERN = r'<li class="w_80pc"><a href="([^"]+)" target="_blank">'
