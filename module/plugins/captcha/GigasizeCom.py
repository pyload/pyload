# -*- coding: utf-8 -*-

from module.plugins.captcha.captcha import OCR


class GigasizeCom(OCR):
    __name__    = "GigasizeCom"
    __type__    = "ocr"
    __version__ = "0.10"

    __description__ = """Gigasize.com ocr plugin"""
    __license__     = "GPLv3"
    __authors__     = [("pyLoad Team", "admin@pyload.org")]


    def __init__(self):
        OCR.__init__(self)


    def get_captcha(self, image):
        self.load_image(image)
        self.threshold(2.8)
        self.run_tesser(True, False, False, True)
        return self.result_captcha
