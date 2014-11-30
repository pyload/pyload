# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class FiredriveComFolder(DeadCrypter):
    __name__    = "FiredriveComFolder"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/share/.+'
    __config__  = []

    __description__ = """Firedrive.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(FiredriveComFolder)
