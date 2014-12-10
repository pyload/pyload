# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class FiletramCom(SimpleCrypter):
    __name    = "FiletramCom"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?filetram\.com/[^/]+/.+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Filetram.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("igel", "igelkun@myopera.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'\s+(http://.+)'
    NAME_PATTERN = r'<title>(?P<N>.+?) - Free Download'
