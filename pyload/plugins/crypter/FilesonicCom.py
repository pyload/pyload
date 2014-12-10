# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadCrypter import DeadCrypter, create_getInfo


class FilesonicCom(DeadCrypter):
    __name    = "FilesonicCom"
    __type    = "crypter"
    __version = "0.12"

    __pattern = r'http://(?:www\.)?filesonic\.com/folder/\w+'

    __description = """Filesonic.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(FilesonicCom)
