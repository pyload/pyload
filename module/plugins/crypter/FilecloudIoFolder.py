# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class FilecloudIoFolder(SimpleCrypter):
    __name__    = "FilecloudIoFolder"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(filecloud\.io|ifile\.it)/_\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Filecloud.io folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'href="(http://filecloud\.io/\w+)" title'
    NAME_PATTERN = r'>(?P<N>.+?) - filecloud\.io<'


getInfo = create_getInfo(FilecloudIoFolder)
