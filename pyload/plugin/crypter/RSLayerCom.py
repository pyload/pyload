# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadCrypter import DeadCrypter


class RSLayerCom(DeadCrypter):
    __name    = "RSLayerCom"
    __type    = "crypter"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?rs-layer\.com/directory-'
    __config  = []

    __description = """RS-Layer.com decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("hzpz", "")]
