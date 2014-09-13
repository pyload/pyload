# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FilecloudIoFolder(SimpleCrypter):
    __name__ = "FilecloudIoFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?(filecloud\.io|ifile\.it)/_\w+'

    __description__ = """Filecloud.io folder decrypter plugin"""
    __author_name__ = "Walter Purcaro"
    __author_mail__ = "vuolter@gmail.com"

    LINK_PATTERN = r'href="(http://filecloud.io/\w+)" title'
    TITLE_PATTERN = r'>(?P<title>.+?) - filecloud.io<'
