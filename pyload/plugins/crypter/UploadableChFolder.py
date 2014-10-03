# -*- coding: utf-8 -*-

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadableChFolder(SimpleCrypter):
    __name__ = "UploadableChFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?uploadable\.ch/list/\w+'

    __description__ = """Uploadable.ch folder decrypter plugin"""
    __author_name__ = ("guidobelix", "Walter Purcaro")
    __author_mail__ = ("guidobelix@hotmail.it", "vuolter@gmail.com")


    LINK_PATTERN = r'"(.+?)" class="icon_zipfile">'
    TITLE_PATTERN = r'<div class="folder"><span>&nbsp;</span>(?P<title>.+?)</div>'
    OFFLINE_PATTERN = r'We are sorry... The URL you entered cannot be found on the server.'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'
