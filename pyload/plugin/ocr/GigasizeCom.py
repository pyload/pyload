# -*- coding: utf-8 -*-

from pyload.plugin.OCR import OCR


class GigasizeCom(OCR):
    __name    = "GigasizeCom"
    __type    = "ocr"
    __version = "0.10"

    __description = """Gigasize.com ocr plugin"""
    __license     = "GPLv3"
    __authors     = [("pyLoad Team", "admin@pyload.org")]


    def __init__(self):
        OCR.__init__(self)


    def get_captcha(self, image):
        self.load_image(image)
        self.threshold(2.8)
        self.run_tesser(True, False, False, True)
        return self.result_captcha
