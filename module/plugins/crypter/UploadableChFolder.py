# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadableChFolder(SimpleCrypter):
    __name__    = "UploadableChFolder"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?uploadable\.ch/list/\w+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """ Uploadable.ch folder decrypter plugin """
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'"(.+?)" class="icon_zipfile">'
    NAME_PATTERN = r'<div class="folder"><span>&nbsp;</span>(.+?)</div>'
    OFFLINE_PATTERN = r'We are sorry... The URL you entered cannot be found on the server.'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'
