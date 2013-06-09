# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter

class CrockoComFolder(SimpleCrypter):
    __name__ = "CrockoComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?crocko.com/f/.*"
    __version__ = "0.01"
    __description__ = """Crocko.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    LINK_PATTERN = r'<td class="last"><a href="([^"]+)">download</a>'