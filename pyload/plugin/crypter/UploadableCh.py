# -*- coding: utf-8 -*-

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class UploadableCh(SimpleCrypter):
    __name    = "UploadableCh"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?uploadable\.ch/list/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Uploadable.ch folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("guidobelix", "guidobelix@hotmail.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'"(.+?)" class="icon_zipfile">'
    NAME_PATTERN = r'<div class="folder"><span>&nbsp;</span>(?P<N>.+?)</div>'
    OFFLINE_PATTERN = r'We are sorry... The URL you entered cannot be found on the server.'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'
