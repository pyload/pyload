# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class SecureUploadEu(XFileSharingPro):
    __name__ = "SecureUploadEu"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?secureupload\.eu/(\w){12}(/\w+)"
    __version__ = "0.01"
    __description__ = """SecureUpload.eu hoster plugin"""
    __author_name__ = ("z00nx")
    __author_mail__ = ("z00nx0@gmail.com")

    HOSTER_NAME = "secureupload.eu"
    FILE_INFO_PATTERN = '<h3>Downloading (?P<N>[^<]+) \((?P<S>[^<]+)\)</h3>'
    FILE_OFFLINE_PATTERN = 'The file was removed|File Not Found'

getInfo = create_getInfo(SecureUploadEu)
