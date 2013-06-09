# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter

class FshareVnFolder(SimpleCrypter):
    __name__ = "FshareVnFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?fshare.vn/folder/.*"
    __version__ = "0.01"
    __description__ = """Fshare.vn Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    LINK_PATTERN = r'<li class="w_80pc"><a href="([^"]+)" target="_blank">'