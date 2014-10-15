# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class RapidfileshareNetFolder(SimpleCrypter):
    __name__ = "RapidfileshareNetFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?rapidfileshare\.net/users/\w+/\d+/\w+'

    __description__ = """Rapidfileshare.net folder decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    LINK_PATTERN = r'<a href="(.+?)" target="_blank">.+?</a>'
    TITLE_PATTERN = r'<Title>Files of \w+: ([^<]+) folder<'
