# -*- coding: utf-8 -*-

from ..internal.DeadCrypter import DeadCrypter


class FiredriveComFolder(DeadCrypter):
    __name__ = "FiredriveComFolder"
    __type__ = "crypter"
    __version__ = "0.09"
    __status__ = "stable"

    __pattern__ = r'https?://(?:www\.)?(firedrive|putlocker)\.com/share/.+'
    __config__ = [("activated", "bool", "Activated", True)]

    __description__ = """Firedrive.com folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]
