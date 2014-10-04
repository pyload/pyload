# -*- coding: utf-8 -*-

from module.plugins.internal.DeadCrypter import DeadCrypter


class MultiuploadCom(DeadCrypter):
    __name__ = "MultiuploadCom"
    __type__ = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?multiupload\.(com|nl)/\w+'

    __description__ = """ MultiUpload.com decrypter plugin """
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"
