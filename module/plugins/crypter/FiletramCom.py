# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FiletramCom(SimpleCrypter):
    __name__    = "FiletramCom"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?filetram\.com/[^/]+/.+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Filetram.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'\s+(http://.+)'
    NAME_PATTERN = r'<title>(.+?) - Free Download'
