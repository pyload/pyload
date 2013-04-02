# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DataHuFolder(SimpleCrypter):
    __name__ = "DataHuFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?data.hu/dir/\w+"
    __version__ = "0.01"
    __description__ = """Data.hu Folder Plugin"""
    __author_name__ = ("crash")

    LINK_PATTERN = r"<a href='(http://data\.hu/get/.+)' target='_blank'>\1</a>"
    TITLE_PATTERN = ur'<title>(.+) Let\xf6lt\xe9se</title>'
