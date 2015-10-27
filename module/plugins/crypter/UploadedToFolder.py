# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class UploadedToFolder(SimpleCrypter):
    __name__    = "UploadedToFolder"
    __type__    = "crypter"
    __version__ = "0.47"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/\w+'
    __config__  = [("activated"            , "bool", "Activated"                                        , True),
                   ("use_premium"          , "bool", "Use premium account if available"                 , True),
                   ("use_subfolder"        , "bool", "Save package to subfolder"                        , True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package"              , True),
                   ("max_wait"             , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """UploadedTo decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    NAME_PATTERN         = r'<title>(?P<N>.+?)<'
    OFFLINE_PATTERN      = r'>Page not found'
    TEMP_OFFLINE_PATTERN = r'<title>uploaded\.net - Maintenance'

    LINK_PATTERN = r'<h2><a href="(.+?)"'


getInfo = create_getInfo(UploadedToFolder)
