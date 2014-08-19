# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class RSLayerCom(DeadCrypter):
    __name__ = "RSLayerCom"
    __version__ = "0.21"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?rs-layer.com/directory-'

    __description__ = """RS-Layer.com decrypter plugin"""
    __author_name__ = "hzpz"
    __author_mail__ = None
