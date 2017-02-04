# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class BigfileToFolder(SimpleCrypter):
    __name__    = "BigfileToFolder"
    __type__    = "crypter"
    __version__ = "0.09"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(?:uploadable\.ch|bigfile\.to)/list/\w+'
    __config__  = [("activated"         , "bool"          , "Activated"                                        , True     ),
                   ("use_premium"       , "bool"          , "Use premium account if available"                 , True     ),
                   ("folder_per_package", "Default;Yes;No", "Create folder for each package"                   , "Default"),
                   ("max_wait"          , "int"           , "Reconnect if waiting time is greater than minutes", 10       )]

    __description__ = """bigfile.to folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("guidobelix",     "guidobelix@hotmail.it"     ),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("GammaC0de",      "nitzo2001[AT]yahoo[DOT]com")]


    URL_REPLACEMENTS = [("https?://uploadable\.ch", "https://bigfile.to")]

    LINK_PATTERN = r'"(.+?)" class="icon_zipfile">'
    NAME_PATTERN = r'<div class="folder"><span>&nbsp;</span>(?P<N>.+?)</div>'
    OFFLINE_PATTERN = r'We are sorry... The URL you entered cannot be found on the server.'
    TEMP_OFFLINE_PATTERN = r'<div class="icon_err">'
