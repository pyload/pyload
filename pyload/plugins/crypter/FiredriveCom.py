# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class FiredriveCom(DeadCrypter):
    __name    = "FiredriveCom"
    __type    = "crypter"
    __version = "0.03"

    __pattern = r'https?://(?:www\.)?(firedrive|putlocker)\.com/share/.+'
    __config  = []

    __description = """Firedrive.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


getInfo = create_getInfo(FiredriveCom)
