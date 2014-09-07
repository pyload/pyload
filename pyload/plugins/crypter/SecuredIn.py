# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter


class SecuredIn(DeadCrypter):
    __name__ = "SecuredIn"
    __type__ = "crypter"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?secured\.in/download-[\d]+-[\w]{8}\.html'

    __description__ = """Secured.in decrypter plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"
