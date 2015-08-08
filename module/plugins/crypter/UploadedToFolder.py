# -*- coding: utf-8 -*-

import re
import urlparse

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class UploadedToFolder(SimpleCrypter):
    __name__    = "UploadedToFolder"
    __type__    = "crypter"
    __version__ = "0.44"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """UploadedTo decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    NAME_PATTERN         = r'<title>(?P<N>.+?)<'
    OFFLINE_PATTERN      = r'>Page not found'
    TEMP_OFFLINE_PATTERN = r'<title>uploaded\.net - Maintenance'

    LINK_PATTERN = r'<h2><a href="(.+?)"'


getInfo = create_getInfo(UploadedToFolder)
