# -*- coding: utf-8 -*-

from pyload.plugins.OCR import OCR


class GigasizeCom(OCR):
    __name__ = "GigasizeCom"
    __type__ = "ocr"
    __version__ = "0.1"

    __description__ = """Gigasize.com ocr plugin"""
    __author_name__ = "pyLoad Team"
    __author_mail__ = "admin@pyload.org"


    def __init__(self):
        OCR.__init__(self)

    def get_captcha(self, image):
        self.load_image(image)
        self.threshold(2.8)
        self.run_tesser(True, False, False, True)
        return self.result_captcha
