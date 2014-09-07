# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class SecureUploadEu(XFileSharingPro):
    __name__ = "SecureUploadEu"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?secureupload\.eu/(\w){12}(/\w+)'

    __description__ = """SecureUpload.eu hoster plugin"""
    __author_name__ = "z00nx"
    __author_mail__ = "z00nx0@gmail.com"

    HOSTER_NAME = "secureupload.eu"

    FILE_INFO_PATTERN = r'<h3>Downloading (?P<N>[^<]+) \((?P<S>[^<]+)\)</h3>'
    OFFLINE_PATTERN = r'The file was removed|File Not Found'


getInfo = create_getInfo(SecureUploadEu)
