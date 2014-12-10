# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class NosvideoCom(SimpleCrypter):
    __name    = "NosvideoCom"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?nosvideo\.com/\?v=\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Nosvideo.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("igel", "igelkun@myopera.com")]


    LINK_PATTERN = r'href="(http://(?:w{3}\.)?nosupload\.com/\?d=\w+)"'
    NAME_PATTERN = r'<[tT]itle>Watch (?P<N>.+?)<'
