# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class UploadableChFolder(SimpleCrypter):
    __name__    = "UploadableChFolder"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?uploadable\.ch/list/\w+'
    __config__  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Uploadable.ch folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix", "guidobelix@hotmail.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    LINK_PATTERN = r'"(.+?)" class="icon_zipfile">'
    NAME_PATTERN = r'<div class="folder"><span>&nbsp;</span>(?P<N>.+?)</div>'
    OFFLINE_PATTERN = r'We are sorry... The URL you entered cannot be found on the server.'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'


getInfo = create_getInfo(UploadableChFolder)
