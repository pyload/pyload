# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FiletramCom(SimpleCrypter):
    __name__    = "FiletramCom"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?filetram\.com/[^/]+/.+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Filetram.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com"),
                       ("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'\s+(http://.+)'
    NAME_PATTERN = r'<title>(?P<N>.+?) - Free Download'


getInfo = create_getInfo(FiletramCom)
