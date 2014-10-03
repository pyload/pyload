# -*- coding: utf-8 -*-

from pyload.plugins.internal.XFileSharingPro import XFileSharingPro, create_getInfo


class SecureUploadEu(XFileSharingPro):
    __name__ = "SecureUploadEu"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?secureupload\.eu/\w{12}'

    __description__ = """SecureUpload.eu hoster plugin"""
    __author_name__ = "z00nx"
    __author_mail__ = "z00nx0@gmail.com"


    HOSTER_NAME = "secureupload.eu"

    FILE_INFO_PATTERN = r'<h3>Downloading (?P<N>[^<]+) \((?P<S>[^<]+)\)</h3>'


getInfo = create_getInfo(SecureUploadEu)
