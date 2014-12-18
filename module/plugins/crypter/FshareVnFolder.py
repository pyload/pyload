# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FshareVnFolder(SimpleCrypter):
    __name__    = "FshareVnFolder"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?fshare\.vn/folder/.*'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Fshare.vn folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<li class="w_80pc"><a href="([^"]+)" target="_blank">'


getInfo = create_getInfo(FshareVnFolder)
