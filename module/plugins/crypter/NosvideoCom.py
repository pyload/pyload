# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class NosvideoCom(SimpleCrypter):
    __name__    = "NosvideoCom"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?nosvideo\.com/\?v=\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Nosvideo.com decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("igel", "igelkun@myopera.com")]


    LINK_PATTERN = r'href="(http://(?:w{3}\.)?nosupload\.com/\?d=\w+)"'
    NAME_PATTERN = r'<[tT]itle>Watch (?P<N>.+?)<'


getInfo = create_getInfo(NosvideoCom)
