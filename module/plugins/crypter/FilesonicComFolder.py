# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class FilesonicComFolder(DeadCrypter):
    __name__    = "FilesonicComFolder"
    __type__    = "crypter"
    __version__ = "0.12"

    __pattern__ = r'http://(?:www\.)?filesonic\.com/folder/\w+'

    __description__ = """Filesonic.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
