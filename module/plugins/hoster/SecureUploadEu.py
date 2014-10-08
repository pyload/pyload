# -*- coding: utf-8 -*-

from module.plugins.internal.XFSPHoster import XFSPHoster, create_getInfo


class SecureUploadEu(XFSPHoster):
    __name__ = "SecureUploadEu"
    __type__ = "hoster"
    __version__ = "0.04"

    __pattern__ = r'https?://(?:www\.)?secureupload\.eu/\w{12}'

    __description__ = """SecureUpload.eu hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("z00nx", "z00nx0@gmail.com")]


    HOSTER_NAME = "secureupload.eu"

    FILE_INFO_PATTERN = r'<h3>Downloading (?P<N>[^<]+) \((?P<S>[^<]+)\)</h3>'


getInfo = create_getInfo(SecureUploadEu)
