# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class FilecloudIo(SimpleCrypter):
    __name    = "FilecloudIo"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)?(filecloud\.io|ifile\.it)/_\w+'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """Filecloud.io folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'href="(http://filecloud\.io/\w+)" title'
    NAME_PATTERN = r'>(?P<N>.+?) - filecloud\.io<'
