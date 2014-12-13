# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class SecureUploadEu(XFSHoster):
    __name    = "SecureUploadEu"
    __type    = "hoster"
    __version = "0.05"

    __pattern = r'https?://(?:www\.)?secureupload\.eu/\w{12}'

    __description = """SecureUpload.eu hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com")]


    HOSTER_DOMAIN = "secureupload.eu"

    INFO_PATTERN = r'<h3>Downloading (?P<N>[^<]+) \((?P<S>[^<]+)\)</h3>'


getInfo = create_getInfo(SecureUploadEu)
