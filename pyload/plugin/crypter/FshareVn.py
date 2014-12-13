# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class FshareVn(SimpleCrypter):
    __name    = "FshareVn"
    __type    = "crypter"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?fshare\.vn/folder/.*'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Fshare.vn folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    LINK_PATTERN = r'<li class="w_80pc"><a href="([^"]+)" target="_blank">'
