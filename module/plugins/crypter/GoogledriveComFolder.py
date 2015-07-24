# -*- coding: utf-8 -*

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class GoogledriveComFolder(SimpleCrypter):
    __name__    = "GoogledriveCom"
    __type__    = "crypter"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?drive\.google\.com/folderview\?.*id=\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),  #: Overrides pyload.config['general']['folder_per_package']
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Drive.google.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r"folderName: '(?P<N>.+?)'"
    LINK_PATTERN    = r'\[,"\w+"(?:,,".+?")?,"(.+?)"'
    OFFLINE_PATTERN = r'<TITLE>'


getInfo = create_getInfo(GoogledriveComFolder)
